
import pytest
from mysql.connector import Error as MySQLError

from app.utils.excecoes import (
    MENSAGEM_ERRO_BANCO,
    tratar_erro_de_dados
)


def test_decorator_converte_erro_mysql_em_tupla_padrao():
    @tratar_erro_de_dados
    def funcao():
        raise MySQLError("Falha simulada.")

    assert funcao() == (
        False,
        MENSAGEM_ERRO_BANCO,
        None
    )


def test_decorator_preserva_retorno_normal():
    @tratar_erro_de_dados
    def funcao(x):
        return True, "ok", x

    assert funcao(7) == (True, "ok", 7)


def test_decorator_nao_engole_value_error():
    @tratar_erro_de_dados
    def funcao():
        raise ValueError("Regra de negócio.")

    with pytest.raises(ValueError):
        funcao()


def test_decorator_nao_engole_permission_error():
    @tratar_erro_de_dados
    def funcao():
        raise PermissionError("Acesso negado.")

    with pytest.raises(PermissionError):
        funcao()


def test_decorator_preserva_nome_da_funcao():
    @tratar_erro_de_dados
    def minha_funcao():
        return True

    assert minha_funcao.__name__ == "minha_funcao"
