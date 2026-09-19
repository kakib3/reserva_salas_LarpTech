from app.services import reservas_service


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


def cancelar_reserva(id_reserva, id_usuario):
    resultado = reservas_service.cancelar_reserva(id_reserva, id_usuario)

    if resultado is False:
        return False, "Não foi possível cancelar: reserva não encontrada, não autorizada ou já cancelada.", None

    return True, "Reserva cancelada com sucesso.", None


def alterar_reserva(id_reserva, id_usuario, nova_sala, nova_data, novo_inicio, novo_fim):
    try:
        resultado = reservas_service.alterar_reserva(id_reserva, id_usuario, nova_sala, nova_data, novo_inicio, novo_fim)
    except ValueError as e:
        return False, str(e), None

    if resultado is False:
        return False, "Não foi possível alterar a reserva houve conflito de horário", None

    return True, "Reserva alterada com sucesso.", None

    
def aprovar_reserva(id_reserva):
    resultado = reservas_service.aprovar_reserva(id_reserva)

    if resultado is False:
        return False, "Não foi possível aprovar: reserva não encontrada ou não está pendente.", None

    return True, "Reserva aprovada com sucesso.", None


def negar_reserva(id_reserva):
    resultado = reservas_service.negar_reserva(id_reserva)

    if resultado is False:
        return False, "Não foi possível negar: reserva não encontrada ou não está pendente.", None

    return True, "Reserva negada com sucesso.", None