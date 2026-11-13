import functools
import logging
from mysql.connector import Error as MySQLError

log = logging.getLogger(__name__)

MENSAGEM_ERRO_BANCO = "Não foi possível acessar os dados. Tente novamente."


def tratar_erro_de_dados(func):
    """Padroniza o retorno dos controllers quando o banco falha.

    Devolve (False, mensagem_amigavel, None) e registra a causa real no log.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except MySQLError:
            log.exception("Falha de acesso ao banco em %s", func.__name__)
            return False, MENSAGEM_ERRO_BANCO, None

    return wrapper
