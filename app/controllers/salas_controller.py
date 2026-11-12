from app.services import sala_service
from app.utils.excecoes import tratar_erro_de_dados


@tratar_erro_de_dados
def cadastrar_sala(nome, capacidade, predio, andar, status, tipo_sala, id_solicitante):
    try:
        resultado = sala_service.criar_sala(
            nome, capacidade, predio, andar, status, tipo_sala, id_solicitante
        )
    except (ValueError, PermissionError) as e:
        return False, str(e), None

    return True, "Sala cadastrada com sucesso.", resultado


@tratar_erro_de_dados
def editar_sala(id_sala, nome, capacidade, predio, andar, tipo_sala, id_solicitante):
    try:
        resultado = sala_service.alterar_sala(
            id_sala, nome, capacidade, predio, andar, tipo_sala, id_solicitante
        )
    except (ValueError, PermissionError) as e:
        return False, str(e), None

    if resultado is False:
        return False, "Sala não encontrada.", None

    return True, "Sala atualizada com sucesso.", resultado


@tratar_erro_de_dados
def mudar_status_sala(id_sala, novo_status, id_solicitante):
    try:
        resultado = sala_service.alterar_status_sala(
            id_sala, novo_status, id_solicitante
        )
    except (ValueError, PermissionError) as e:
        return False, str(e), None

    if resultado is False:
        return False, "Sala não encontrada ou já está nesse status.", None

    return True, f"Status da sala alterado para '{novo_status}'.", None


@tratar_erro_de_dados
def ocultar_sala(id_sala, id_solicitante):
    try:
        sala_service.ocultar_sala(id_sala, id_solicitante)
    except PermissionError as e:
        return False, str(e), None

    return True, "Sala ocultada com sucesso.", None


@tratar_erro_de_dados
def mostrar_sala(id_sala, id_solicitante):
    try:
        sala_service.mostrar_sala(id_sala, id_solicitante)
    except PermissionError as e:
        return False, str(e), None

    return True, "Sala exibida com sucesso.", None


@tratar_erro_de_dados
def obter_sala(id_sala):
    sala = sala_service.buscar_sala_por_id(id_sala)

    if sala is None:
        return False, "Sala não encontrada.", None

    return True, "", sala


# Mantém o retorno direto da Service, como já era esperado pelas chamadas existentes.
def listar_todas_salas():
    return sala_service.listar_salas()

@tratar_erro_de_dados
def consultar_salas(id_usuario, somente_disponiveis=False, capacidade_minima=0, predio=None):
    try:
        salas = sala_service.consultar_salas(
            id_usuario,
            somente_disponiveis,
            capacidade_minima,
            predio
        )
    except (ValueError, PermissionError) as e:
        return False, str(e), None

    return True, "", salas


@tratar_erro_de_dados
def consultar_predios(id_usuario):
    try:
        predios = sala_service.consultar_predios(id_usuario)
    except (ValueError, PermissionError) as e:
        return False, str(e), None

    return True, "", predios


@tratar_erro_de_dados
def consultar_salas_para_reserva(id_usuario):
    try:
        salas = sala_service.consultar_salas_para_reserva(id_usuario)
    except (ValueError, PermissionError) as e:
        return False, str(e), None

    return True, "", salas


@tratar_erro_de_dados
def consultar_salas_disponiveis(limite=5):
    if not isinstance(limite, int) or limite < 1:
        return False, "O limite deve ser um número inteiro positivo.", None

    salas = sala_service.consultar_salas_disponiveis(limite)

    return True, "", salas


@tratar_erro_de_dados
def consultar_disponibilidade(id_sala, data_consulta):
    resultado = sala_service.consultar_disponibilidade(
        id_sala,
        data_consulta
    )

    if resultado is None:
        return False, "Sala não encontrada.", None

    return True, "", resultado

@tratar_erro_de_dados
def pode_gerenciar_pendencias(id_usuario):
    resultado = reservas_service.pode_gerenciar_pendencias(
        id_usuario
    )

    return True, "", resultado
