from app.services import usuarios_service


def cadastrar_usuario(nome, email, telefone, role, senha):
    try:
        resultado = usuarios_service.criar_usuario(nome, email, telefone, role, senha)
    except ValueError as e:
        return False, str(e), None

    if resultado is False:
        return False, "Já existe um usuário cadastrado com esse email.", None

    return True, "Usuário cadastrado com sucesso.", resultado


def fazer_login(email, senha):
    resultado = usuarios_service.autenticar_usuario(email, senha)

    if resultado is False:
        return False, "Email ou senha inválidos.", None

    return True, f"Bem-vindo, {resultado.nome}!", resultado


def editar_usuario(id_usuario, nome, email, telefone, role):
    try:
        resultado = usuarios_service.alterar_usuario(id_usuario, nome, email, telefone, role)
    except ValueError as e:
        return False, str(e), None

    if resultado is False:
        return False, "Usuário não encontrado ou email já em uso por outro usuário.", None

    return True, "Dados atualizados com sucesso.", resultado


def trocar_senha(id_usuario, senha_atual, nova_senha):
    try:
        resultado = usuarios_service.alterar_senha(id_usuario, senha_atual, nova_senha)
    except ValueError as e:
        return False, str(e), None

    if resultado is False:
        return False, "Usuário não encontrado ou senha atual incorreta.", None

    return True, "Senha alterada com sucesso.", None


def desativar_usuario(id_usuario):
    resultado = usuarios_service.desativar_usuario(id_usuario)

    if resultado is False:
        return False, "Usuário não encontrado ou já está inativo.", None

    return True, "Usuário desativado com sucesso.", None


def obter_usuario(id_usuario):
    usuario = usuarios_service.buscar_usuario_por_id(id_usuario)

    if usuario is None:
        return False, "Usuário não encontrado.", None

    return True, "", usuario


def listar_todos_usuarios():
    return usuarios_service.listar_usuarios()
