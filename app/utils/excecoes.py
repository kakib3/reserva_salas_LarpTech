import functools


class ErroDeDados(Exception):
    """Falha ao ler ou gravar o armazenamento (CSV).

    Não herda de ValueError nem de OSError de propósito: assim os
    `except ValueError` e `except PermissionError` dos controllers não a
    capturam por engano e a exibem como erro de regra de negócio.
    """

    def __init__(self, mensagem_usuario):
        super().__init__(mensagem_usuario)
        self.mensagem_usuario = mensagem_usuario


def tratar_erro_de_dados(func):
    """Para controllers que retornam (sucesso, mensagem, objeto).

    Converte ErroDeDados em (False, mensagem_amigavel, None), o mesmo
    formato usado nos erros de regra de negócio.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ErroDeDados as e:
            return False, e.mensagem_usuario, None

    return wrapper