"""Contrato dos controllers usados pelas views de gerenciamento."""
from mysql.connector import Error as MySQLError

from app.controllers import salas_controller, usuarios_controller
from app.utils.excecoes import MENSAGEM_ERRO_BANCO


# ---------------- validar_dados_usuario ----------------
def test_validar_dados_usuario_validos():
    assert usuarios_controller.validar_dados_usuario(
        "Maria Silva", "maria@email.com", "69999990000", "Aluno", "Senha123"
    ) == (True, "", [])


def test_validar_dados_usuario_devolve_todos_os_erros():
    sucesso, mensagem, erros = usuarios_controller.validar_dados_usuario(
        "A", "invalido", "1", "Chefe", "curta"
    )

    assert sucesso is False
    assert mensagem == ""
    assert len(erros) == 5


def test_validar_dados_usuario_sem_senha_nao_confere_senha():
    """Na edição não há senha: passar None não gera erro de senha."""
    sucesso, _, erros = usuarios_controller.validar_dados_usuario(
        "Maria Silva", "maria@email.com", "69999990000", "Aluno"
    )

    assert sucesso is True and erros == []


# ---------------- listar_todas_salas ----------------
def test_listar_todas_salas_segue_o_contrato_de_tupla(monkeypatch):
    salas = [{"id_sala": 1, "nome": "Sala01"}]
    monkeypatch.setattr(salas_controller.sala_service, "listar_salas", lambda: salas)

    assert salas_controller.listar_todas_salas() == (True, "", salas)


def test_listar_todas_salas_trata_erro_do_banco(monkeypatch):
    def falha():
        raise MySQLError("banco fora do ar")

    monkeypatch.setattr(salas_controller.sala_service, "listar_salas", falha)

    assert salas_controller.listar_todas_salas() == (False, MENSAGEM_ERRO_BANCO, None)
