
import logging

from app.models.conexao import conectar_banco
from app.models.reserva import Reserva
from app.models.constantes import (
    PapelUsuario,
    StatusReserva,
    StatusSala,
    TipoSala,
)
from app.services import usuarios_service
from app.utils import salas_ocultas
from app.utils.relogio import hoje
from app.utils.horarios import normalizar_horarios
from app.messaging import notificacoes_service


logger = logging.getLogger(__name__)


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


def obter_conflitos_horario(
    id_sala,
    data,
    hora_inicio,
    hora_fim,
    id_reserva_ignorar=None
):
    """Retorna reservas ativas que se sobrepõem ao horário informado."""

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
            id_sala,
            data,
            StatusReserva.CONFIRMADA,
            StatusReserva.PENDENTE,
            hora_fim,
            hora_inicio
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


def verificar_conflito_horario(
    id_sala,
    data,
    hora_inicio,
    hora_fim,
    id_reserva_ignorar=None
):
    conflitos = obter_conflitos_horario(
        id_sala,
        data,
        hora_inicio,
        hora_fim,
        id_reserva_ignorar
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
        None,
        id_usuario,
        id_sala,
        data,
        hora_inicio,
        hora_fim,
        None,
        None
    )

    _validar_reserva(reserva_obj)

    conflitos = obter_conflitos_horario(
        id_sala,
        data,
        hora_inicio,
        hora_fim
    )

    permitido, ids_substituidos = _resolver_prioridade(
        _papel_do_usuario(id_usuario),
        conflitos
    )

    if not permitido:
        return False

    status = _definir_status_reserva(id_sala)

    if status is None:
        return False

    # Em salas que exigem aprovação, reservas de alunos
    # só são substituídas quando a reserva do professor é aprovada.
    if status == StatusReserva.PENDENTE:
        ids_substituidos = []

    reserva_obj.status = status
    reserva_obj.criado_em = hoje()

    valores = (
        id_usuario,
        id_sala,
        data,
        hora_inicio,
        hora_fim,
        status,
        reserva_obj.criado_em
    )

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor()

        _cancelar_reservas_substituidas(cursor, ids_substituidos)

        cursor.execute(
            """INSERT INTO reservas
               (id_usuario, id_sala, data_reserva, hora_inicio,
                hora_fim, status_reserva, criado_em)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            valores
        )

        conexao.commit()
        reserva_obj.id = cursor.lastrowid

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

    # A notificação só acontece depois que a reserva é persistida.
    if status == StatusReserva.CONFIRMADA:
        _tentar_notificar(
            notificacoes_service.notificar_reserva_confirmada,
            reserva_obj
        )

    elif status == StatusReserva.PENDENTE:
        _tentar_notificar(
            notificacoes_service.notificar_reserva_pendente,
            reserva_obj
        )

    return reserva_obj


def cancelar_reserva(id_reserva, id_usuario):
    if not usuarios_service.checar_usuario_ativo(id_usuario):
        return False

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """SELECT id_usuario, status_reserva
               FROM reservas
               WHERE id_reserva = %s""",
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
            """UPDATE reservas
               SET status_reserva = %s
               WHERE id_reserva = %s
               AND id_usuario = %s
               AND status_reserva IN (%s, %s)""",
            (
                StatusReserva.CANCELADA,
                id_reserva,
                id_usuario,
                StatusReserva.CONFIRMADA,
                StatusReserva.PENDENTE
            )
        )

        if cursor.rowcount == 0:
            return False

        conexao.commit()
        return True

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


def alterar_reserva(
    id_reserva,
    id_usuario,
    nova_sala,
    nova_data,
    novo_inicio,
    novo_fim
):
    if not usuarios_service.checar_usuario_ativo(id_usuario):
        return False

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """SELECT id_usuario, status_reserva
               FROM reservas
               WHERE id_reserva = %s""",
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

    if salas_ocultas.esta_oculta(nova_sala):
        return False

    reserva_obj = Reserva(
        id_reserva,
        id_usuario,
        nova_sala,
        nova_data,
        novo_inicio,
        novo_fim,
        reserva["status_reserva"],
        None
    )

    _validar_reserva(reserva_obj)

    conflitos = obter_conflitos_horario(
        nova_sala,
        nova_data,
        novo_inicio,
        novo_fim,
        id_reserva_ignorar=id_reserva
    )

    permitido, ids_substituidos = _resolver_prioridade(
        _papel_do_usuario(id_usuario),
        conflitos
    )

    if not permitido:
        return False

    status = _definir_status_reserva(nova_sala)

    if status is None:
        return False

    if status == StatusReserva.PENDENTE:
        ids_substituidos = []

    valores = (
        nova_sala,
        nova_data,
        novo_inicio,
        novo_fim,
        status,
        id_reserva,
        id_usuario,
        reserva["status_reserva"]
    )

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor()

        _cancelar_reservas_substituidas(cursor, ids_substituidos)

        cursor.execute(
            """UPDATE reservas
               SET id_sala = %s,
                   data_reserva = %s,
                   hora_inicio = %s,
                   hora_fim = %s,
                   status_reserva = %s
               WHERE id_reserva = %s
               AND id_usuario = %s
               AND status_reserva = %s""",
            valores
        )

        if cursor.rowcount == 0:
            return False

        conexao.commit()
        return True

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


# Métodos utilitários

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
    reserva.validar_nao_passado()


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
    """Decide se o solicitante pode ocupar o horário e quais reservas cancelar.

    Regras:
    - Sem conflito: permitido.
    - Apenas o Professor pode assumir o horário de outra reserva,
      e somente quando as reservas conflitantes pertencem a Alunos.
    - Se existir conflito com outro Professor ou Admin,
      prevalece a regra de quem reservou primeiro.
    """

    if not conflitos:
        return True, []

    if papel_solicitante != PapelUsuario.PROFESSOR:
        return False, []

    if any(
        conflito["papel"] != PapelUsuario.ALUNO
        for conflito in conflitos
    ):
        return False, []

    return True, [
        conflito["id_reserva"]
        for conflito in conflitos
    ]


def _cancelar_reservas_substituidas(cursor, ids_reservas):
    """Cancela reservas substituídas dentro da transação recebida."""

    if not ids_reservas:
        return

    marcadores = ", ".join(["%s"] * len(ids_reservas))

    cursor.execute(
        f"""UPDATE reservas
            SET status_reserva = %s
            WHERE id_reserva IN ({marcadores})
            AND status_reserva IN (%s, %s)""",
        (
            StatusReserva.CANCELADA,
            *ids_reservas,
            StatusReserva.CONFIRMADA,
            StatusReserva.PENDENTE
        )
    )


def aprovar_reserva(id_reserva, id_usuario):
    if not usuarios_service.checar_admin(id_usuario):
        return False

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """SELECT id_usuario, id_sala, data_reserva,
                      hora_inicio, hora_fim, status_reserva, criado_em
               FROM reservas
               WHERE id_reserva = %s""",
            (id_reserva,)
        )

        dados = cursor.fetchone()

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

    if not dados:
        return False

    if dados["status_reserva"] != StatusReserva.PENDENTE:
        return False

    if not verificar_sala_disponivel(dados["id_sala"]):
        return False

    # A prioridade é do dono da reserva, não do Admin que aprova.
    # Se o dono for Professor, poderá assumir horários de Alunos.
    conflitos = obter_conflitos_horario(
        dados["id_sala"],
        dados["data_reserva"],
        dados["hora_inicio"],
        dados["hora_fim"],
        id_reserva_ignorar=id_reserva
    )

    permitido, ids_substituidos = _resolver_prioridade(
        _papel_do_usuario(dados["id_usuario"]),
        conflitos
    )

    if not permitido:
        return False

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor()

        _cancelar_reservas_substituidas(cursor, ids_substituidos)

        cursor.execute(
            """UPDATE reservas
               SET status_reserva = %s
               WHERE id_reserva = %s
               AND status_reserva = %s""",
            (
                StatusReserva.CONFIRMADA,
                id_reserva,
                StatusReserva.PENDENTE
            )
        )

        if cursor.rowcount == 0:
            return False

        conexao.commit()

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

    dados["status_reserva"] = StatusReserva.CONFIRMADA

    reserva_obj = _montar_objeto_reserva(id_reserva, dados)

    _tentar_notificar(
        notificacoes_service.notificar_reserva_aprovada,
        reserva_obj
    )

    return True


def negar_reserva(id_reserva, id_usuario):
    if not usuarios_service.checar_admin(id_usuario):
        return False

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """SELECT id_usuario, id_sala, data_reserva,
                      hora_inicio, hora_fim, status_reserva, criado_em
               FROM reservas
               WHERE id_reserva = %s""",
            (id_reserva,)
        )

        dados = cursor.fetchone()

        if not dados:
            return False

        if dados["status_reserva"] != StatusReserva.PENDENTE:
            return False

        cursor.execute(
            """UPDATE reservas
               SET status_reserva = %s
               WHERE id_reserva = %s
               AND status_reserva = %s""",
            (
                StatusReserva.CANCELADA,
                id_reserva,
                StatusReserva.PENDENTE
            )
        )

        if cursor.rowcount == 0:
            return False

        conexao.commit()

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

    dados["status_reserva"] = StatusReserva.CANCELADA

    reserva_obj = _montar_objeto_reserva(id_reserva, dados)

    _tentar_notificar(
        notificacoes_service.notificar_reserva_recusada,
        reserva_obj
    )

    return True


# Consultas utilizadas pelas views

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
            normalizar_horarios(resultado)

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
            normalizar_horarios(reserva)

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
            normalizar_horarios(reserva)

            reserva["pode_alterar"] = (
                reserva["status_reserva"] in StatusReserva.ATIVAS
            )

        return resultado

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


def pode_gerenciar_pendencias(id_usuario):
    return usuarios_service.checar_admin(id_usuario)


# Helpers da mensageria

def _tentar_notificar(funcao_notificacao, reserva):
    """Evita que uma falha na notificação comprometa a operação principal."""

    try:
        funcao_notificacao(reserva)

    except Exception:
        logger.exception(
            "Falha ao enviar notificação da reserva %s.",
            getattr(reserva, "id", None)
        )


def _montar_objeto_reserva(id_reserva, dados):
    """Reconstrói o objeto Reserva a partir dos dados retornados pelo MySQL."""

    return Reserva(
        id_reserva,
        dados["id_usuario"],
        dados["id_sala"],
        dados["data_reserva"],
        dados["hora_inicio"],
        dados["hora_fim"],
        dados["status_reserva"],
        dados.get("criado_em")
    )