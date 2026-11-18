"""usuarios_service contra um MySQL de verdade."""
import pytest

from app.services import usuarios_service
from app.utils import seguranca

SENHA = "Senha123"


# ---- criar_usuario ---------------------------------------------------------
def test_criar_usuario_grava_com_hash_e_status_ativo(banco):
    resultado = usuarios_service.criar_usuario(
        "Maria Silva", "maria@teste.com", "69999990000", "Aluno", SENHA
    )

    assert resultado is not False
    linha = banco.um("SELECT * FROM usuarios WHERE email = %s", ("maria@teste.com",))
    assert linha["nome"] == "Maria Silva"
    assert linha["papel"] == "Aluno"          # valor do enum do banco
    assert linha["status_usuario"] == "Ativo"
    assert linha["senha"] != SENHA            # nunca texto puro
    assert seguranca.verificar_senha(SENHA, linha["senha"])


def test_email_duplicado_retorna_false_e_nao_duplica(banco):
    usuarios_service.criar_usuario("Maria", "maria@teste.com", "69999990000", "Aluno", SENHA)

    segundo = usuarios_service.criar_usuario("Outra", "maria@teste.com", "69988880000", "Aluno", SENHA)

    assert segundo is False
    assert banco.contar("usuarios") == 1


def test_email_e_unico_sem_diferenciar_maiusculas(criar_usuario_db):
    """Comportamento da collation utf8mb4_unicode_ci: só um MySQL de verdade mostra isso."""
    criar_usuario_db(email="maria@teste.com")

    assert usuarios_service.verificar_email_disponivel("MARIA@TESTE.COM") is False
    assert usuarios_service.verificar_email_disponivel("outra@teste.com") is True


def test_dados_invalidos_levantam_valueerror_e_nao_gravam(banco):
    with pytest.raises(ValueError):
        usuarios_service.criar_usuario("Maria", "email-invalido", "69999990000", "Aluno", SENHA)

    with pytest.raises(ValueError):
        usuarios_service.criar_usuario("Maria", "m@teste.com", "69999990000", "Aluno", "curta")

    assert banco.contar("usuarios") == 0


def test_criar_admin_exige_admin_solicitante(banco, id_aluno):
    with pytest.raises(PermissionError):
        usuarios_service.criar_usuario(
            "Novo Admin", "novo@teste.com", "69999990000", "Admin", SENHA, id_solicitante=id_aluno
        )

    assert banco.contar("usuarios", "papel = 'Admin'") == 0


def test_admin_cria_outro_admin(banco, id_admin):
    resultado = usuarios_service.criar_usuario(
        "Novo Admin", "novo@teste.com", "69999990000", "Admin", SENHA, id_solicitante=id_admin
    )

    assert resultado is not False
    assert banco.contar("usuarios", "papel = 'Admin'") == 2


# ---- autenticar_usuario ----------------------------------------------------
def test_autenticar_usuario(criar_usuario_db):
    criar_usuario_db(nome="Maria", email="maria@teste.com")

    usuario = usuarios_service.autenticar_usuario("maria@teste.com", SENHA)

    assert usuario is not False
    assert usuario.email == "maria@teste.com"
    assert usuario.role == "Aluno"


def test_autenticar_recusa_senha_errada_email_inexistente_e_inativo(criar_usuario_db):
    criar_usuario_db(email="maria@teste.com")
    criar_usuario_db(email="inativo@teste.com", status="Inativo")

    assert usuarios_service.autenticar_usuario("maria@teste.com", "SenhaErrada1") is False
    assert usuarios_service.autenticar_usuario("ninguem@teste.com", SENHA) is False
    assert usuarios_service.autenticar_usuario("inativo@teste.com", SENHA) is False


# ---- alterar_usuario -------------------------------------------------------
def test_alterar_usuario_mantendo_o_proprio_email(banco, id_aluno):
    """Regressão: o e-mail do próprio usuário não conta como 'já em uso'."""
    resultado = usuarios_service.alterar_usuario(
        id_aluno, id_aluno, "Nome Novo", "aluno@teste.com", "69911112222", "Aluno"
    )

    assert resultado is not False
    linha = banco.um("SELECT nome, telefone FROM usuarios WHERE id_usuario = %s", (id_aluno,))
    assert linha == {"nome": "Nome Novo", "telefone": "69911112222"}


def test_alterar_usuario_com_email_de_outro_retorna_false_e_nao_altera(banco, id_aluno, id_professor):
    resultado = usuarios_service.alterar_usuario(
        id_aluno, id_aluno, "Aluno", "prof@teste.com", "69999990000", "Aluno"
    )

    assert resultado is False
    assert banco.um("SELECT email FROM usuarios WHERE id_usuario = %s", (id_aluno,))["email"] == "aluno@teste.com"


def test_aluno_nao_edita_outro_usuario_nem_o_proprio_papel(id_aluno, id_professor):
    with pytest.raises(PermissionError):
        usuarios_service.alterar_usuario(
            id_aluno, id_professor, "X Y", "prof@teste.com", "69999990000", "Professor"
        )

    with pytest.raises(PermissionError):
        usuarios_service.alterar_usuario(
            id_aluno, id_aluno, "Aluno", "aluno@teste.com", "69999990000", "Admin"
        )


def test_admin_altera_papel_de_outro_usuario(banco, id_admin, id_aluno):
    usuarios_service.alterar_usuario(
        id_admin, id_aluno, "Aluno Teste", "aluno@teste.com", "69999990000", "Professor"
    )

    assert banco.um("SELECT papel FROM usuarios WHERE id_usuario = %s", (id_aluno,))["papel"] == "Professor"


def test_ultimo_admin_nao_pode_ser_rebaixado(banco, id_admin):
    with pytest.raises(ValueError):
        usuarios_service.alterar_usuario(
            id_admin, id_admin, "Admin Teste", "admin@teste.com", "69999990000", "Professor"
        )

    assert banco.um("SELECT papel FROM usuarios WHERE id_usuario = %s", (id_admin,))["papel"] == "Admin"


# ---- alterar_senha ---------------------------------------------------------
def test_alterar_senha_troca_o_hash_no_banco(banco, id_aluno):
    resultado = usuarios_service.alterar_senha(id_aluno, id_aluno, SENHA, "NovaSenha456")

    assert resultado is not False
    assert usuarios_service.autenticar_usuario("aluno@teste.com", "NovaSenha456") is not False
    assert usuarios_service.autenticar_usuario("aluno@teste.com", SENHA) is False


def test_alterar_senha_com_senha_atual_errada_retorna_false(banco, id_aluno):
    antes = banco.um("SELECT senha FROM usuarios WHERE id_usuario = %s", (id_aluno,))["senha"]

    assert usuarios_service.alterar_senha(id_aluno, id_aluno, "Errada123", "NovaSenha456") is False
    assert banco.um("SELECT senha FROM usuarios WHERE id_usuario = %s", (id_aluno,))["senha"] == antes


def test_so_o_proprio_usuario_altera_a_senha(id_aluno, id_professor):
    with pytest.raises(PermissionError):
        usuarios_service.alterar_senha(id_professor, id_aluno, SENHA, "NovaSenha456")


# ---- desativar_usuario -----------------------------------------------------
def test_admin_desativa_usuario(banco, id_admin, id_aluno):
    assert usuarios_service.desativar_usuario(id_admin, id_aluno) is not False

    assert banco.um("SELECT status_usuario FROM usuarios WHERE id_usuario = %s", (id_aluno,))["status_usuario"] == "Inativo"
    assert usuarios_service.autenticar_usuario("aluno@teste.com", SENHA) is False


def test_desativar_regras_de_estado_e_permissao(id_admin, id_aluno, criar_usuario_db):
    with pytest.raises(PermissionError):
        usuarios_service.desativar_usuario(id_aluno, id_admin)

    with pytest.raises(ValueError):
        usuarios_service.desativar_usuario(id_admin, id_admin)

    id_inativo = criar_usuario_db(status="Inativo")
    assert usuarios_service.desativar_usuario(id_admin, id_inativo) is False
    assert usuarios_service.desativar_usuario(id_admin, 9999) is False
