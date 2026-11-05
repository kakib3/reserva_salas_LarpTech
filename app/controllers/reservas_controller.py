from app.services import reservas_service
from app.models.dados import carregar_reservas
from app.services import usuarios_service
from app.utils.excecoes import tratar_erro_de_dados


@tratar_erro_de_dados
def reservar_sala(id_usuario, id_sala, data, hora_inicio, hora_fim):
    try:
        resultado = reservas_service.criar_reserva(id_usuario, id_sala, data, hora_inicio, hora_fim)
    except ValueError as e:
        return False, str(e), None

    if resultado is False:
        return False, "Não foi possível reservar: sala indisponível ou conflito de horário.", None

    if resultado.status == "Pendente":
        return True, "Reserva registrada como pendente (aguardando confirmação).", resultado

    return True, "Reserva confirmada com sucesso.", resultado


@tratar_erro_de_dados
def cancelar_reserva(id_reserva, id_usuario):
    resultado = reservas_service.cancelar_reserva(id_reserva, id_usuario)

    if resultado is False:
        return False, "Não foi possível cancelar: reserva não encontrada, não autorizada ou já cancelada.", None

    return True, "Reserva cancelada com sucesso.", None


@tratar_erro_de_dados
def alterar_reserva(id_reserva, id_usuario, nova_sala, nova_data, novo_inicio, novo_fim):
    try:
        resultado = reservas_service.alterar_reserva(id_reserva, id_usuario, nova_sala, nova_data, novo_inicio, novo_fim)
    except ValueError as e:
        return False, str(e), None

    if resultado is False:
        return False, "Não foi possível alterar a reserva houve conflito de horário", None

    return True, "Reserva alterada com sucesso.", None


@tratar_erro_de_dados
def aprovar_reserva(id_reserva, id_solicitante):
    if not usuarios_service.checar_admin(id_solicitante):
        return False, "Não foi possível aprovar: usuário sem permissão de administrador.", None

    reservas = carregar_reservas()
    reserva = reservas[reservas["idReserva"] == id_reserva]

    if not reserva.empty:
        id_sala = reserva.iloc[0]["idSala"]
        if not reservas_service.verificar_sala_disponivel(id_sala):
            return False, "Não foi possível aprovar: a sala está em manutenção ou indisponível.", None

    resultado = reservas_service.aprovar_reserva(id_reserva, id_solicitante)

    if resultado is False:
        return False, "Não foi possível aprovar: verifique se você tem permissão e se a reserva está pendente.", None

    return True, "Reserva aprovada com sucesso.", None


@tratar_erro_de_dados
def negar_reserva(id_reserva, id_solicitante):
    resultado = reservas_service.negar_reserva(id_reserva, id_solicitante)

    if resultado is False:
        return False, "Não foi possível negar: reserva não encontrada ou não está pendente.", None

    return True, "Reserva negada com sucesso.", None