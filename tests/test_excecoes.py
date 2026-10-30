import pytest

from app.utils.excecoes import ErroDeDados, tratar_erro_de_dados


def test_erro_de_dados_nao_herda_de_valueerror_nem_oserror():
    assert not issubclass(ErroDeDados, (ValueError, OSError))


def test_decorator_converte_erro_de_dados_em_tupla_padrao():
    @tratar_erro_de_dados
    def funcao():
        raise ErroDeDados("Dados ilegíveis.")

    assert funcao() == (False, "Dados ilegíveis.", None)


def test_decorator_preserva_retorno_normal():
    @tratar_erro_de_dados
    def funcao(x):
        return True, "ok", x

    assert funcao(7) == (True, "ok", 7)


def test_decorator_nao_engole_outras_excecoes():
    @tratar_erro_de_dados
    def funcao():
        raise ValueError("regra de negócio")

    with pytest.raises(ValueError):
        funcao()


def test_erro_de_dados_passa_pelo_except_valueerror_do_controller():
    """Um except ValueError dentro do controller não pode interceptar ErroDeDados."""

    @tratar_erro_de_dados
    def controller():
        try:
            raise ErroDeDados("Falha no armazenamento.")
        except ValueError:
            return False, "REGRA DE NEGÓCIO", None

    assert controller() == (False, "Falha no armazenamento.", None)