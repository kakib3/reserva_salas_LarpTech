from app.models.conexao import conectar_banco
from app.models.reserva import Reserva
from datetime import date
from app.services import usuarios_service
from app.models.constantes import StatusReserva, StatusSala, TipoSala

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


def verificar_conflito_horario(id_sala, data, hora_inicio, hora_fim, id_reserva_ignorar=None):
    
    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        sql = """SELECT id_reserva FROM reservas
                 WHERE id_sala = %s
                 AND data_reserva = %s
                 AND status_reserva IN (%s, %s)
                 AND hora_inicio < %s
                 AND hora_fim > %s"""

        valores = (
            id_sala, data,
            StatusReserva.CONFIRMADA,
            StatusReserva.PENDENTE,
            hora_fim, hora_inicio
        )

        if id_reserva_ignorar is not None:
            sql += " AND id_reserva != %s"
            valores += (id_reserva_ignorar,)

        cursor.execute(sql, valores)

        return cursor.fetchone() is not None

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

def criar_reserva(id_usuario, id_sala, data, hora_inicio, hora_fim):
    if not usuarios_service.checar_usuario_ativo(id_usuario):
        return False

    if not verificar_sala_disponivel(id_sala):
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