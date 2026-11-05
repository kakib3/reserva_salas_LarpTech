from app.services import usuarios_service
from app.utils.excecoes import tratar_erro_de_dados


@tratar_erro_de_dados
def cadastrar_usuario(nome, email, telefone, role, senha, id_solicitante=None):
    try:
        resultado = usuarios_service.criar_usuario(nome, email, telefone, role, senha, id_solicitante)
    except (ValueError, PermissionError) as e:
        return False, str(e), None

    if resultado is False:
        return False, "Já existe um usuário cadastrado com esse email.", None

    return True, "Usuário cadastrado com sucesso.", resultado


@tratar_erro_de_dados
def fazer_login(email, senha):
    resultado = usuarios_service.autenticar_usuario(email, senha)

    if resultado is False:
        return False, "Email ou senha inválidos.", None

    return True, f"Bem-vindo, {resultado.nome}!", resultado


@tratar_erro_de_dados
def editar_usuario(id_usuario, nome, email, telefone, role, id_solicitante):
    try:
        resultado = usuarios_service.alterar_usuario(id_solicitante, id_usuario, nome, email, telefone, role)
    except (ValueError, PermissionError) as e:
        return False, str(e), None

    if resultado is False:
        return False, "Usuário não encontrado ou email já em uso por outro usuário.", None

    return True, "Dados atualizados com sucesso.", resultado


@tratar_erro_de_dados
def trocar_senha(id_usuario, senha_atual, nova_senha, id_solicitante):
    try:
        resultado = usuarios_service.alterar_senha(id_solicitante, id_usuario, senha_atual, nova_senha)
    except (ValueError, PermissionError) as e:
        return False, str(e), None

    if resultado is False:
        return False, "Usuário não encontrado ou senha atual incorreta.", None

    return True, "Senha alterada com sucesso.", None


@tratar_erro_de_dados
def desativar_usuario(id_usuario, id_solicitante):
    try:
        resultado = usuarios_service.desativar_usuario(id_solicitante, id_usuario)
    except (ValueError, PermissionError) as e:
        return False, str(e), None

    if resultado is False:
        return False, "Usuário não encontrado ou já está inativo.", None

    return True, "Usuário desativado com sucesso.", None


@tratar_erro_de_dados
def obter_usuario(id_usuario, id_solicitante):
    try:
        usuario = usuarios_service.obter_usuario(id_solicitante, id_usuario)
    except PermissionError as e:
        return False, str(e), None

    if usuario is None:
        return False, "Usuário não encontrado.", None

    return True, "", usuario


@tratar_erro_de_dados
def listar_todos_usuarios(id_solicitante):
    try:
        usuarios = usuarios_service.listar_usuarios(id_solicitante)
    except PermissionError as e:
        return False, str(e), None

    return True, "", usuarios