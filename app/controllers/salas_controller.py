from app.services import sala_service


def cadastrar_sala(nome, capacidade, predio, andar, status, tipo_sala):
    try:
        resultado = sala_service.criar_sala(nome, capacidade, predio, andar, status, tipo_sala)
    except ValueError as e:
        return False, str(e), None

    return True, "Sala cadastrada com sucesso.", resultado


def editar_sala(id_sala, nome, capacidade, predio, andar, tipo_sala):
    try:
        resultado = sala_service.alterar_sala(id_sala, nome, capacidade, predio, andar, tipo_sala)
    except ValueError as e:
        return False, str(e), None

    if resultado is False:
        return False, "Sala não encontrada.", None

    return True, "Sala atualizada com sucesso.", resultado


def mudar_status_sala(id_sala, novo_status):
    try:
        resultado = sala_service.alterar_status_sala(id_sala, novo_status)
    except ValueError as e:
        return False, str(e), None

    if resultado is False:
        return False, "Sala não encontrada ou já está nesse status.", None

    return True, f"Status da sala alterado para '{novo_status}'.", None


def obter_sala(id_sala):
    sala = sala_service.buscar_sala_por_id(id_sala)

    if sala is None:
        return False, "Sala não encontrada.", None

    return True, "", sala


def listar_todas_salas():
    return sala_service.listar_salas()
