"""Testes do hash de senha nos services de usuário, com um banco falso em memória
(não dependem do MySQL)."""
import pytest

from app.services import usuarios_service
from app.utils.seguranca import gerar_hash_senha

SENHA = "Senha@123"


class _BancoFalso:
    def __init__(self):
        self.usuarios = {}
        self._proximo_id = 1

    def adicionar(self, nome, email, papel, senha, status="Ativo"):
        id_usuario = self._proximo_id
        self._proximo_id += 1
        self.usuarios[id_usuario] = {
            "id_usuario": id_usuario, "nome": nome, "email": email,
            "telefone": "92 99999-9999", "papel": papel, "senha": senha,
            "status_usuario": status,
        }
        return id_usuario

    def por_email(self, email):
        return next((u for u in self.usuarios.values() if u["email"] == email), None)


class _Cursor:
    def __init__(self, banco):
        self.banco = banco
        self._resultado = None
        self.lastrowid = None

    def execute(self, sql, params=()):
        sql = " ".join(sql.split())

        if sql.startswith("SELECT id_usuario FROM usuarios WHERE email"):
            self._resultado = self.banco.por_email(params[0])
        elif sql.startswith("SELECT * FROM usuarios WHERE email"):
            self._resultado = self.banco.por_email(params[0])
        elif sql.startswith("SELECT * FROM usuarios WHERE id_usuario"):
            self._resultado = self.banco.usuarios.get(params[0])
        elif sql.startswith("INSERT INTO usuarios"):
            nome, email, telefone, papel, senha, status = params
            self.banco.adicionar(nome, email, papel, senha, status)
        elif sql.startswith("UPDATE usuarios SET senha"):
            senha, id_usuario = params
            self.banco.usuarios[id_usuario]["senha"] = senha
        else:
            raise AssertionError(f"SQL não previsto no teste: {sql}")

    def fetchone(self):
        return self._resultado

    def close(self):
        pass


class _Conexao:
    def __init__(self, banco):
        self.banco = banco

    def cursor(self, dictionary=False):
        return _Cursor(self.banco)

    def commit(self):
        pass

    def close(self):
        pass


@pytest.fixture
def banco(monkeypatch):
    banco = _BancoFalso()
    monkeypatch.setattr(usuarios_service, "conectar_banco", lambda: _Conexao(banco))
    return banco


def test_criar_usuario_grava_hash_e_nao_a_senha(banco):
    assert usuarios_service.criar_usuario(
        "Ana Silva", "ana@teste.com", "92 99999-9999", "Aluno", SENHA
    ) is True

    gravada = banco.por_email("ana@teste.com")["senha"]

    assert gravada != SENHA
    assert gravada.startswith("$2")


def test_login_com_senha_correta_devolve_o_usuario(banco):
    banco.adicionar("Ana Silva", "ana@teste.com", "Aluno", gerar_hash_senha(SENHA))

    usuario = usuarios_service.autenticar_usuario("ana@teste.com", SENHA)

    assert usuario is not False
    assert usuario.email == "ana@teste.com"


def test_login_com_senha_errada_falha(banco):
    banco.adicionar("Ana Silva", "ana@teste.com", "Aluno", gerar_hash_senha(SENHA))

    assert usuarios_service.autenticar_usuario("ana@teste.com", "Outra@123") is False


def test_login_de_usuario_inexistente_falha(banco):
    assert usuarios_service.autenticar_usuario("ninguem@teste.com", SENHA) is False


def test_login_de_usuario_inativo_falha_mesmo_com_senha_correta(banco):
    banco.adicionar("Ana Silva", "ana@teste.com", "Aluno", gerar_hash_senha(SENHA), status="Inativo")

    assert usuarios_service.autenticar_usuario("ana@teste.com", SENHA) is False


def test_login_recusa_senha_antiga_ainda_em_texto_puro(banco):
    """Conta não migrada: a senha no banco não é um hash, então o login falha."""
    banco.adicionar("Ana Silva", "ana@teste.com", "Aluno", SENHA)

    assert usuarios_service.autenticar_usuario("ana@teste.com", SENHA) is False


def test_alterar_senha_troca_para_a_nova_e_invalida_a_antiga(banco):
    id_usuario = banco.adicionar("Ana Silva", "ana@teste.com", "Aluno", gerar_hash_senha(SENHA))

    assert usuarios_service.alterar_senha(id_usuario, id_usuario, SENHA, "Nova@12345") is True

    assert banco.usuarios[id_usuario]["senha"].startswith("$2")
    assert usuarios_service.autenticar_usuario("ana@teste.com", "Nova@12345") is not False
    assert usuarios_service.autenticar_usuario("ana@teste.com", SENHA) is False


def test_alterar_senha_com_senha_atual_errada_nao_altera(banco):
    hash_original = gerar_hash_senha(SENHA)
    id_usuario = banco.adicionar("Ana Silva", "ana@teste.com", "Aluno", hash_original)

    assert usuarios_service.alterar_senha(id_usuario, id_usuario, "Errada@123", "Nova@12345") is False
    assert banco.usuarios[id_usuario]["senha"] == hash_original


def test_alterar_senha_recusa_nova_senha_curta(banco):
    id_usuario = banco.adicionar("Ana Silva", "ana@teste.com", "Aluno", gerar_hash_senha(SENHA))

    with pytest.raises(ValueError):
        usuarios_service.alterar_senha(id_usuario, id_usuario, SENHA, "abc")
