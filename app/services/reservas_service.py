from app.models.conexao import conectar_banco
from app.models.reserva import Reserva
from datetime import date, time, timedelta
from app.services import usuarios_service
from app.utils import salas_ocultas
from app.models.constantes import PapelUsuario, StatusReserva, StatusSala, TipoSala

def verificar_sala_disponivel(id_sala):
    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            "SELECT status_sala FROM salas WHERE id_sala = %s",
            (id_sala,)
        )
        resultado = cursor.fetchone()

        if not resultado:
            return False

        return resultado["status_sala"] == StatusSala.DISPONIVEL

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


def obter_conflitos_horario(id_sala, data, hora_inicio, hora_fim, id_reserva_ignorar=None):
    """Retorna as reservas ativas que se sobrepõem ao horário, com o papel do dono de cada uma."""
    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        sql = """SELECT r.id_reserva, u.papel
                 FROM reservas r
                 LEFT JOIN usuarios u ON u.id_usuario = r.id_usuario
                 WHERE r.id_sala = %s
                 AND r.data_reserva = %s
                 AND r.status_reserva IN (%s, %s)
                 AND r.hora_inicio < %s
                 AND r.hora_fim > %s"""

        valores = (
            id_sala, data,
            StatusReserva.CONFIRMADA,
            StatusReserva.PENDENTE,
            hora_fim, hora_inicio
        )

        if id_reserva_ignorar is not None:
            sql += " AND r.id_reserva != %s"
            valores += (id_reserva_ignorar,)

        cursor.execute(sql, valores)

        return cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


def verificar_conflito_horario(id_sala, data, hora_inicio, hora_fim, id_reserva_ignorar=None):
    conflitos = obter_conflitos_horario(
        id_sala, data, hora_inicio, hora_fim, id_reserva_ignorar
    )

    return len(conflitos) > 0

def criar_reserva(id_usuario, id_sala, data, hora_inicio, hora_fim):
    if not usuarios_service.checar_usuario_ativo(id_usuario):
        return False

    if not verificar_sala_disponivel(id_sala):
        return False

    if salas_ocultas.esta_oculta(id_sala):
        return False

    reserva_obj = Reserva(
        None, id_usuario, id_sala, data,
        hora_inicio, hora_fim, None, None
    )

    _validar_reserva(reserva_obj)

    if verificar_conflito_horario(id_sala, data, hora_inicio, hora_fim):
        return False

    status = _definir_status_reserva(id_sala)

    if status is None:
        return False

    reserva_obj.status = status
    reserva_obj.criado_em = date.today()

    valores = (
        id_usuario, id_sala, data, hora_inicio,
        hora_fim, status, reserva_obj.criado_em
    )

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor()

        cursor.execute("""INSERT INTO reservas
                       (id_usuario, id_sala, data_reserva, hora_inicio,
                       hora_fim, status_reserva, criado_em)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""", valores)

        conexao.commit()
        reserva_obj.id = cursor.lastrowid

        return reserva_obj

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


def cancelar_reserva(id_reserva,id_usuario):
    if not usuarios_service.checar_usuario_ativo(id_usuario):
        return False

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """SELECT id_usuario, status_reserva
               FROM reservas WHERE id_reserva = %s""",
            (id_reserva,)
        )
        reserva = cursor.fetchone()

        if not reserva:
            return False

        if reserva["id_usuario"] != id_usuario:
            return False

        if reserva["status_reserva"] not in StatusReserva.ATIVAS:
            return False

        cursor.execute(
            "UPDATE reservas SET status_reserva = %s WHERE id_reserva = %s",
            (StatusReserva.CANCELADA, id_reserva)
        )

        conexao.commit()
        return True

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

def alterar_reserva(id_reserva, id_usuario, nova_sala, nova_data, novo_inicio, novo_fim):
    if not usuarios_service.checar_usuario_ativo(id_usuario):
        return False

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """SELECT id_usuario, status_reserva
               FROM reservas WHERE id_reserva = %s""",
            (id_reserva,)
        )
        reserva = cursor.fetchone()

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

    if not reserva:
        return False

    if reserva["id_usuario"] != id_usuario:
        return False

    if reserva["status_reserva"] not in StatusReserva.ATIVAS:
        return False

    if not verificar_sala_disponivel(nova_sala):
        return False

    reserva_obj = Reserva(
        id_reserva, id_usuario, nova_sala, nova_data,
        novo_inicio, novo_fim, reserva["status_reserva"], None
    )

    _validar_reserva(reserva_obj)

    if verificar_conflito_horario(
        nova_sala, nova_data, novo_inicio, novo_fim,
        id_reserva_ignorar=id_reserva
    ):
        return False

    status = _definir_status_reserva(nova_sala)

    if status is None:
        return False

    valores = (
        nova_sala, nova_data, novo_inicio,
        novo_fim, status, id_reserva
    )

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor()

        cursor.execute("""UPDATE reservas
                       SET id_sala = %s,
                       data_reserva = %s,
                       hora_inicio = %s,
                       hora_fim = %s,
                       status_reserva = %s
                       WHERE id_reserva = %s""", valores)

        conexao.commit()
        return True

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

#Métodos Utilitários
def descobre_tipo_sala(id_sala):
    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            "SELECT tipo_sala FROM salas WHERE id_sala = %s",
            (id_sala,)
        )
        sala = cursor.fetchone()

        if sala:
            return sala["tipo_sala"]

        return None

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

def _validar_reserva(reserva):
    reserva.validar_horario()
    reserva.validar_intervalo()
    reserva.validar_horario_funcionamento()
    reserva.validar_dia_util()

def _definir_status_reserva(id_sala):
    sala_tipo = descobre_tipo_sala(id_sala)

    if sala_tipo in TipoSala.PRECISA_APROVACAO:
        return StatusReserva.PENDENTE

    elif sala_tipo in (TipoSala.SALA, TipoSala.REUNIAO):
        return StatusReserva.CONFIRMADA

    return None


def _papel_do_usuario(id_usuario):
    usuario = usuarios_service.buscar_usuario_por_id(id_usuario)

    if usuario is None:
        return None

    return usuario.role

def _resolver_prioridade(papel_solicitante, conflitos):
    """Decide se o solicitante pode ocupar o horário e quais reservas perdem o slot.

    Retorna (permitido, ids_a_cancelar).

    - Sem conflito: permitido, nada a cancelar.
    - Só o Professor pode assumir o horário de outra reserva, e apenas de Alunos.
    - Se qualquer reserva em conflito não for de Aluno (outro Professor, Admin),
      vale a regra "quem reservou primeiro fica com o horário".
    """
    if not conflitos:
        return True, []

    if papel_solicitante != PapelUsuario.PROFESSOR:
        return False, []

    if any(c["papel"] != PapelUsuario.ALUNO for c in conflitos):
        return False, []

    return True, [c["id_reserva"] for c in conflitos]

def _cancelar_reservas_substituidas(cursor, ids_reservas):
    """Cancela, na transação do cursor recebido, as reservas que perderam o horário."""
    if not ids_reservas:
        return

    marcadores = ", ".join(["%s"] * len(ids_reservas))

    cursor.execute(
        f"""UPDATE reservas SET status_reserva = %s
            WHERE id_reserva IN ({marcadores})
            AND status_reserva IN (%s, %s)""",
        (StatusReserva.CANCELADA, *ids_reservas,
         StatusReserva.CONFIRMADA, StatusReserva.PENDENTE)
    )


def aprovar_reserva(id_reserva, id_usuario):
    if not usuarios_service.checar_admin(id_usuario):
        return False

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """SELECT id_sala, status_reserva
               FROM reservas WHERE id_reserva = %s""",
            (id_reserva,)
        )
        reserva = cursor.fetchone()

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

    if not reserva:
        return False

    if reserva["status_reserva"] != StatusReserva.PENDENTE:
        return False

    if not verificar_sala_disponivel(reserva["id_sala"]):
        return False

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor()

        cursor.execute(
            "UPDATE reservas SET status_reserva = %s WHERE id_reserva = %s",
            (StatusReserva.CONFIRMADA, id_reserva)
        )

        conexao.commit()
        return True

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

def negar_reserva(id_reserva, id_usuario):
    if not usuarios_service.checar_admin(id_usuario):
        return False

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            "SELECT status_reserva FROM reservas WHERE id_reserva = %s",
            (id_reserva,)
        )
        reserva = cursor.fetchone()

        if not reserva:
            return False

        if reserva["status_reserva"] != StatusReserva.PENDENTE:
            return False

        cursor.execute(
            "UPDATE reservas SET status_reserva = %s WHERE id_reserva = %s",
            (StatusReserva.CANCELADA, id_reserva)
        )

        conexao.commit()
        return True

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()
        
def consultar_proxima_reserva(id_usuario, data_atual):
    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """SELECT r.id_reserva,
                      r.id_usuario,
                      r.id_sala,
                      s.nome AS nome_sala,
                      r.data_reserva,
                      r.hora_inicio,
                      r.hora_fim,
                      r.status_reserva
               FROM reservas r
               INNER JOIN salas s
               ON s.id_sala = r.id_sala
               WHERE r.id_usuario = %s
               AND r.status_reserva IN (%s, %s)
               AND r.data_reserva >= %s
               ORDER BY r.data_reserva, r.hora_inicio
               LIMIT 1""",
            (
                id_usuario,
                StatusReserva.CONFIRMADA,
                StatusReserva.PENDENTE,
                data_atual
            )
        )

        resultado = cursor.fetchone()

        if resultado:
            _normalizar_horarios(resultado)

        return resultado

    finally:
        if cursor is not None:
            cursor.close()

        conexao.close()


def consultar_reservas_pendentes(id_solicitante):
    usuarios_service.exigir_admin(id_solicitante)

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """SELECT r.id_reserva,
                      r.id_usuario,
                      r.id_sala,
                      s.nome AS nome_sala,
                      u.nome AS nome_usuario,
                      u.papel,
                      r.data_reserva,
                      r.hora_inicio,
                      r.hora_fim,
                      r.status_reserva
               FROM reservas r
               INNER JOIN salas s
               ON s.id_sala = r.id_sala
               LEFT JOIN usuarios u
               ON u.id_usuario = r.id_usuario
               WHERE r.status_reserva = %s
               ORDER BY r.data_reserva, r.hora_inicio""",
            (StatusReserva.PENDENTE,)
        )

        resultado = cursor.fetchall()

        for reserva in resultado:
            _normalizar_horarios(reserva)

        return resultado

    finally:
        if cursor is not None:
            cursor.close()

        conexao.close()


def consultar_reservas_usuario(id_usuario):
    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """SELECT r.id_reserva,
                      r.id_usuario,
                      r.id_sala,
                      s.nome AS nome_sala,
                      r.data_reserva,
                      r.hora_inicio,
                      r.hora_fim,
                      r.status_reserva
               FROM reservas r
               LEFT JOIN salas s
               ON s.id_sala = r.id_sala
               WHERE r.id_usuario = %s
               ORDER BY r.data_reserva DESC, r.hora_inicio DESC""",
            (id_usuario,)
        )

        resultado = cursor.fetchall()

        for reserva in resultado:
            _normalizar_horarios(reserva)
            reserva["pode_alterar"] = reserva["status_reserva"] in StatusReserva.ATIVAS

        return resultado

    finally:
        if cursor is not None:
            cursor.close()

        conexao.close()


def pode_gerenciar_pendencias(id_usuario):
    return usuarios_service.checar_admin(id_usuario)


def _normalizar_horarios(reserva):
    for campo in ("hora_inicio", "hora_fim"):
        valor = reserva.get(campo)

        if isinstance(valor, timedelta):
            segundos = int(valor.total_seconds()) % 86400

            reserva[campo] = time(
                segundos // 3600,
                (segundos % 3600) // 60,
                segundos % 60
            )
            
def pode_gerenciar_pendencias(id_usuario):
    return usuarios_service.checar_admin(id_usuario)
