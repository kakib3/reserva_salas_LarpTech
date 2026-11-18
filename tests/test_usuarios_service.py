
import pytest

from app.services import usuarios_service
from app.utils.seguranca import gerar_hash_senha, verificar_senha

# bcrypt é lento de propósito: cada hash é calculado uma única vez para a suíte inteira.
HASHES = {
    senha: gerar_hash_senha(senha)
    for senha in ("Admin@123", "Aluno@123", "Prof@123")
}


# ============================================================
# BANCO DE DADOS SIMULADO
# ============================================================

class BancoFake:
    def __init__(self):
        self.usuarios = [
            {
                "id_usuario": 1,
                "nome": "Administrador",
                "email": "admin@email.com",
                "telefone": "69999999999",
                "papel": "Admin",
                "senha": HASHES["Admin@123"],
                "status_usuario": "Ativo",
            },
            {
                "id_usuario": 2,
                "nome": "Aluno Teste",
                "email": "aluno@email.com",
                "telefone": "69988888888",
                "papel": "Aluno",
                "senha": HASHES["Aluno@123"],
                "status_usuario": "Ativo",
            },
            {
                "id_usuario": 3,
                "nome": "Professor Teste",
                "email": "prof@email.com",
                "telefone": "69977777777",
                "papel": "Professor",
                "senha": HASHES["Prof@123"],
                "status_usuario": "Ativo",
            },
        ]

        self.proximo_id = 4

    def conectar(self):
        return ConexaoFake(self)


class ConexaoFake:
    def __init__(self, banco):
        self.banco = banco
        self.fechada = False
        self.commits = 0

    def cursor(self, dictionary=False):
        return CursorFake(self.banco)

    def commit(self):
        self.commits += 1

    def close(self):
        self.fechada = True


class CursorFake:
    def __init__(self, banco):
        self.banco = banco
        self.resultado = []
        self.fechado = False

    def execute(self, sql, valores=None):
        valores = valores or ()
        sql = " ".join(sql.split())

        # Buscar todos os usuários
        if "FROM usuarios" in sql and "WHERE" not in sql:
            campos = [
            "id_usuario",
            "nome",
            "email",
            "telefone",
            "papel",
            "status_usuario",
        ]

            self.resultado = [
                {
                    campo: usuario[campo]
                    for campo in campos
                }
                for usuario in self.banco.usuarios
            ]

        # Buscar usuário por ID
        elif "SELECT * FROM usuarios WHERE id_usuario" in sql:
            id_usuario = valores[0]

            self.resultado = [
                usuario.copy()
                for usuario in self.banco.usuarios
                if usuario["id_usuario"] == id_usuario
            ]

        # Buscar usuário por email
        elif "SELECT * FROM usuarios WHERE email" in sql:
            email = valores[0]

            self.resultado = [
                usuario.copy()
                for usuario in self.banco.usuarios
                if usuario["email"] == email
            ]

        # Verificar email disponível
        elif "SELECT id_usuario FROM usuarios WHERE email" in sql:
            email = valores[0]

            if len(valores) == 2:
                id_ignorado = valores[1]
                self.resultado = [
                    {"id_usuario": usuario["id_usuario"]}
                    for usuario in self.banco.usuarios
                    if usuario["email"] == email
                    and usuario["id_usuario"] != id_ignorado
                ]
            else:
                self.resultado = [
                    {"id_usuario": usuario["id_usuario"]}
                    for usuario in self.banco.usuarios
                    if usuario["email"] == email
                ]

        # Buscar administradores ativos
        elif "SELECT id_usuario FROM usuarios WHERE papel = 'Admin'" in sql:
            self.resultado = [
                {"id_usuario": usuario["id_usuario"]}
                for usuario in self.banco.usuarios
                if usuario["papel"] == "Admin"
                and usuario["status_usuario"] == "Ativo"
            ]

        # Buscar status de um usuário
        elif "SELECT status_usuario FROM usuarios" in sql:
            id_usuario = valores[0]

            self.resultado = [
                {"status_usuario": usuario["status_usuario"]}
                for usuario in self.banco.usuarios
                if usuario["id_usuario"] == id_usuario
            ]

        # Inserir usuário
        elif "INSERT INTO usuarios" in sql:
            nome, email, telefone, papel, senha, status = valores

            self.banco.usuarios.append({
                "id_usuario": self.banco.proximo_id,
                "nome": nome,
                "email": email,
                "telefone": telefone,
                "papel": papel,
                "senha": senha,
                "status_usuario": status,
            })

            self.banco.proximo_id += 1
            self.resultado = []

        # Atualizar dados do usuário
        elif "UPDATE usuarios SET nome" in sql:
            nome, email, telefone, papel, id_usuario = valores

            for usuario in self.banco.usuarios:
                if usuario["id_usuario"] == id_usuario:
                    usuario["nome"] = nome
                    usuario["email"] = email
                    usuario["telefone"] = telefone
                    usuario["papel"] = papel

            self.resultado = []

        # Atualizar senha
        elif "UPDATE usuarios SET senha" in sql:
            senha, id_usuario = valores

            for usuario in self.banco.usuarios:
                if usuario["id_usuario"] == id_usuario:
                    usuario["senha"] = senha

            self.resultado = []

        # Desativar usuário
        elif "UPDATE usuarios SET status_usuario" in sql:
            status, id_usuario = valores

            for usuario in self.banco.usuarios:
                if usuario["id_usuario"] == id_usuario:
                    usuario["status_usuario"] = status

            self.resultado = []

        else:
            raise AssertionError(f"SQL não previsto no teste: {sql}")

    def fetchall(self):
        return self.resultado

    def fetchone(self):
        return self.resultado[0] if self.resultado else None

    def close(self):
        self.fechado = True


@pytest.fixture
def banco(monkeypatch):
    banco_fake = BancoFake()

    monkeypatch.setattr(
        usuarios_service,
        "conectar_banco",
        banco_fake.conectar,
    )

    return banco_fake


# ============================================================
# BUSCA DE USUÁRIOS
# ============================================================

def test_buscar_usuario_por_id(banco):
    usuario = usuarios_service.buscar_usuario_por_id(2)

    assert usuario is not None
    assert usuario.id == 2
    assert usuario.nome == "Aluno Teste"
    assert usuario.role == "Aluno"


def test_buscar_usuario_inexistente(banco):
    usuario = usuarios_service.buscar_usuario_por_id(999)

    assert usuario is None


def test_buscar_usuario_por_email(banco):
    usuario = usuarios_service.buscar_usuario_por_email("aluno@email.com")

    assert usuario is not None
    assert usuario.email == "aluno@email.com"


def test_buscar_email_inexistente(banco):
    usuario = usuarios_service.buscar_usuario_por_email("inexistente@email.com")

    assert usuario is None


def test_listar_usuarios_como_admin(banco):
    usuarios = usuarios_service.listar_usuarios(1)

    assert len(usuarios) == 3
    assert all("senha" not in usuario for usuario in usuarios)


def test_usuario_comum_nao_lista_usuarios(banco):
    with pytest.raises(PermissionError):
        usuarios_service.listar_usuarios(2)


# ============================================================
# VERIFICAÇÃO DE EMAIL
# ============================================================

def test_email_novo_esta_disponivel(banco):
    assert usuarios_service.verificar_email_disponivel(
        "novo@email.com"
    ) is True


def test_email_existente_nao_esta_disponivel(banco):
    assert usuarios_service.verificar_email_disponivel(
        "aluno@email.com"
    ) is False


def test_email_proprio_pode_ser_reutilizado(banco):
    resultado = usuarios_service.verificar_email_disponivel(
        "aluno@email.com",
        id_usuario_ignorar=2,
    )

    assert resultado is True


def test_email_de_outro_usuario_continua_indisponivel(banco):
    resultado = usuarios_service.verificar_email_disponivel(
        "admin@email.com",
        id_usuario_ignorar=2,
    )

    assert resultado is False


# ============================================================
# CRIAÇÃO DE USUÁRIOS
# ============================================================

def test_criar_usuario_aluno(banco):
    resultado = usuarios_service.criar_usuario(
        "Novo Aluno",
        "novo@email.com",
        "69966666666",
        "Aluno",
        "Senha123",
    )

    assert resultado is True
    assert len(banco.usuarios) == 4
    assert banco.usuarios[-1]["email"] == "novo@email.com"


def test_criar_usuario_professor(banco):
    resultado = usuarios_service.criar_usuario(
        "Novo Professor",
        "professor.novo@email.com",
        "69966666666",
        "Professor",
        "Senha123",
    )

    assert resultado is True


def test_admin_pode_criar_outro_admin(banco):
    resultado = usuarios_service.criar_usuario(
        "Novo Admin",
        "novo.admin@email.com",
        "69966666666",
        "Admin",
        "Senha123",
        id_solicitante=1,
    )

    assert resultado is True


def test_usuario_comum_nao_pode_criar_admin(banco):
    with pytest.raises(PermissionError):
        usuarios_service.criar_usuario(
            "Novo Admin",
            "novo.admin@email.com",
            "69966666666",
            "Admin",
            "Senha123",
            id_solicitante=2,
        )


def test_nao_criar_usuario_com_email_duplicado(banco):
    total_antes = len(banco.usuarios)

    resultado = usuarios_service.criar_usuario(
        "Outro Aluno",
        "aluno@email.com",
        "69966666666",
        "Aluno",
        "Senha123",
    )

    assert resultado is False
    assert len(banco.usuarios) == total_antes


def test_criar_usuario_com_email_invalido(banco):
    with pytest.raises(ValueError):
        usuarios_service.criar_usuario(
            "Novo Aluno",
            "email-invalido",
            "69966666666",
            "Aluno",
            "Senha123",
        )


def test_criar_usuario_com_senha_curta(banco):
    with pytest.raises(ValueError):
        usuarios_service.criar_usuario(
            "Novo Aluno",
            "novo@email.com",
            "69966666666",
            "Aluno",
            "123",
        )


# ============================================================
# AUTENTICAÇÃO
# ============================================================

def test_login_com_credenciais_validas(banco):
    usuario = usuarios_service.autenticar_usuario(
        "aluno@email.com",
        "Aluno@123",
    )

    assert usuario is not False
    assert usuario.email == "aluno@email.com"


def test_login_com_senha_incorreta(banco):
    resultado = usuarios_service.autenticar_usuario(
        "aluno@email.com",
        "senha-errada",
    )

    assert resultado is False


def test_login_com_email_inexistente(banco):
    resultado = usuarios_service.autenticar_usuario(
        "inexistente@email.com",
        "Senha123",
    )

    assert resultado is False


def test_usuario_inativo_nao_consegue_logar(banco):
    banco.usuarios[1]["status_usuario"] = "Inativo"

    resultado = usuarios_service.autenticar_usuario(
        "aluno@email.com",
        "Aluno@123",
    )

    assert resultado is False


# ============================================================
# ALTERAÇÃO DE DADOS
# ============================================================

def test_usuario_altera_proprios_dados(banco):
    resultado = usuarios_service.alterar_usuario(
        2,
        2,
        "Aluno Atualizado",
        "aluno.novo@email.com",
        "69966666666",
        "Aluno",
    )

    assert resultado is not False
    assert banco.usuarios[1]["nome"] == "Aluno Atualizado"
    assert banco.usuarios[1]["email"] == "aluno.novo@email.com"


def test_usuario_comum_nao_altera_dados_de_outro(banco):
    with pytest.raises(PermissionError):
        usuarios_service.alterar_usuario(
            2,
            1,
            "Administrador Alterado",
            "admin@email.com",
            "69999999999",
            "Admin",
        )


def test_usuario_comum_nao_pode_se_tornar_admin(banco):
    with pytest.raises(PermissionError):
        usuarios_service.alterar_usuario(
            2,
            2,
            "Aluno Teste",
            "aluno@email.com",
            "69988888888",
            "Admin",
        )


def test_alterar_usuario_inexistente(banco):
    resultado = usuarios_service.alterar_usuario(
        1,
        999,
        "Usuario",
        "usuario@email.com",
        "69966666666",
        "Aluno",
    )

    assert resultado is False


def test_nao_alterar_para_email_de_outro_usuario(banco):
    resultado = usuarios_service.alterar_usuario(
        2,
        2,
        "Aluno Teste",
        "admin@email.com",
        "69988888888",
        "Aluno",
    )

    assert resultado is False
    assert banco.usuarios[1]["email"] == "aluno@email.com"


# ============================================================
# ALTERAÇÃO DE SENHA
# ============================================================

def test_usuario_altera_propria_senha(banco):
    resultado = usuarios_service.alterar_senha(
        2,
        2,
        "Aluno@123",
        "NovaSenha123",
    )

    assert resultado is True
    assert verificar_senha("NovaSenha123", banco.usuarios[1]["senha"])


def test_senha_atual_incorreta_nao_altera_senha(banco):
    resultado = usuarios_service.alterar_senha(
        2,
        2,
        "senha-errada",
        "NovaSenha123",
    )

    assert resultado is False
    assert banco.usuarios[1]["senha"] == HASHES["Aluno@123"]  # continua igual


def test_usuario_nao_altera_senha_de_outro(banco):
    with pytest.raises(PermissionError):
        usuarios_service.alterar_senha(
            2,
            1,
            "Admin@123",
            "NovaSenha123",
        )


def test_nova_senha_curta_e_rejeitada(banco):
    with pytest.raises(ValueError):
        usuarios_service.alterar_senha(
            2,
            2,
            "Aluno@123",
            "123",
        )


# ============================================================
# DESATIVAÇÃO DE USUÁRIOS
# ============================================================

def test_admin_desativa_usuario(banco):
    resultado = usuarios_service.desativar_usuario(1, 2)

    assert resultado is True
    assert banco.usuarios[1]["status_usuario"] == "Inativo"


def test_usuario_comum_nao_desativa_usuario(banco):
    with pytest.raises(PermissionError):
        usuarios_service.desativar_usuario(2, 3)


def test_admin_nao_desativa_a_si_mesmo(banco):
    with pytest.raises(ValueError):
        usuarios_service.desativar_usuario(1, 1)


def test_desativar_usuario_inexistente(banco):
    resultado = usuarios_service.desativar_usuario(1, 999)

    assert resultado is False


def test_desativar_usuario_ja_inativo(banco):
    banco.usuarios[1]["status_usuario"] = "Inativo"

    resultado = usuarios_service.desativar_usuario(1, 2)

    assert resultado is False


# ============================================================
# VERIFICAÇÃO DE PERMISSÕES E STATUS
# ============================================================

def test_checar_admin(banco):
    assert usuarios_service.checar_admin(1) is True
    assert usuarios_service.checar_admin(2) is False
    assert usuarios_service.checar_admin(999) is False


def test_admin_inativo_nao_e_reconhecido_como_admin(banco):
    banco.usuarios[0]["status_usuario"] = "Inativo"

    assert usuarios_service.checar_admin(1) is False


def test_exigir_admin_rejeita_usuario_comum(banco):
    with pytest.raises(PermissionError):
        usuarios_service.exigir_admin(2)


def test_exigir_admin_rejeita_usuario_inexistente(banco):
    with pytest.raises(PermissionError):
        usuarios_service.exigir_admin(999)


def test_checar_usuario_ativo(banco):
    assert usuarios_service.checar_usuario_ativo(2) is True
    assert usuarios_service.checar_usuario_ativo(999) is False


def test_usuario_inativo_nao_e_considerado_ativo(banco):
    banco.usuarios[1]["status_usuario"] = "Inativo"

    assert usuarios_service.checar_usuario_ativo(2) is False


# ============================================================
# REGRA DO ÚLTIMO ADMINISTRADOR
# ============================================================

def test_admin_e_o_unico_admin_ativo(banco):
    assert usuarios_service.eh_ultimo_admin(1) is True


def test_admin_pode_ser_rebaixado_se_existir_outro_admin(banco):
    banco.usuarios.append({
        "id_usuario": 4,
        "nome": "Segundo Admin",
        "email": "segundo@email.com",
        "telefone": "69966666666",
        "papel": "Admin",
        "senha": "Senha123",
        "status_usuario": "Ativo",
    })

    resultado = usuarios_service.eh_ultimo_admin(1)

    assert resultado is False


def test_unico_admin_nao_pode_ser_rebaixado(banco):
    with pytest.raises(ValueError):
        usuarios_service.alterar_usuario(
            1,
            1,
            "Administrador",
            "admin@email.com",
            "69999999999",
            "Professor",
        )


# ============================================================
# CONSULTA DE USUÁRIO E AUTORIZAÇÃO
# ============================================================

def test_usuario_consulta_proprios_dados(banco):
    usuario = usuarios_service.obter_usuario(2, 2)

    assert usuario is not None
    assert usuario.email == "aluno@email.com"


def test_admin_consulta_dados_de_outro_usuario(banco):
    usuario = usuarios_service.obter_usuario(1, 2)

    assert usuario is not None
    assert usuario.email == "aluno@email.com"


def test_usuario_comum_nao_consulta_dados_de_outro(banco):
    with pytest.raises(PermissionError):
        usuarios_service.obter_usuario(2, 1)


def test_consultar_usuario_inexistente(banco):
    usuario = usuarios_service.obter_usuario(1, 999)

    assert usuario is None


def test_telefone_formatado_e_gravado_so_com_digitos(banco):
    resultado = usuarios_service.criar_usuario(
        "Maria Souza", "maria@email.com", "(69) 99999-0000", "Aluno", "Senha123"
    )

    assert resultado is not False
    assert banco.usuarios[-1]["telefone"] == "69999990000"

