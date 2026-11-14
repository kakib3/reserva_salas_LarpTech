
import pytest
from mysql.connector import Error as MySQLError

from app.utils.excecoes import MENSAGEM_ERRO_BANCO
from app.controllers import (
    reservas_controller,
    salas_controller,
    usuarios_controller
)


MSG_ERRO = "Falha simulada no banco de dados."


def _falha_banco(*args, **kwargs):
    raise MySQLError(MSG_ERRO)


@pytest.mark.parametrize(
    "controller, funcao_service, chamada",
    [
        (
            reservas_controller,
            "criar_reserva",
            lambda c: c.reservar_sala(1, 1, None, None, None)
        ),
        (
            reservas_controller,
            "cancelar_reserva",
            lambda c: c.cancelar_reserva(1, 1)
        ),
        (
            reservas_controller,
            "alterar_reserva",
            lambda c: c.alterar_reserva(1, 1, 1, None, None, None)
        ),
        (
            reservas_controller,
            "aprovar_reserva",
            lambda c: c.aprovar_reserva(1, 1)
        ),
        (
            reservas_controller,
            "negar_reserva",
            lambda c: c.negar_reserva(1, 1)
        ),
        (
            usuarios_controller,
            "autenticar_usuario",
            lambda c: c.fazer_login("teste@email.com", "1234")
        ),
    ],
)
def test_controller_converte_erro_mysql(
    monkeypatch,
    controller,
    funcao_service,
    chamada
):
    service = (
        getattr(controller, "reservas_service", None)
        or getattr(controller, "usuarios_service")
    )

    monkeypatch.setattr(
        service,
        funcao_service,
        _falha_banco
    )

    resultado = chamada(controller)

    assert resultado == (
        False,
        MENSAGEM_ERRO_BANCO,
        None
    )


def test_ocultar_sala_converte_erro_mysql(monkeypatch):
    monkeypatch.setattr(
        salas_controller.sala_service,
        "ocultar_sala",
        _falha_banco
    )

    resultado = salas_controller.ocultar_sala(1, 1)

    assert resultado == (
        False,
        MENSAGEM_ERRO_BANCO,
        None
    )


def test_mostrar_sala_converte_erro_mysql(monkeypatch):
    monkeypatch.setattr(
        salas_controller.sala_service,
        "mostrar_sala",
        _falha_banco
    )

    resultado = salas_controller.mostrar_sala(1, 1)

    assert resultado == (
        False,
        MENSAGEM_ERRO_BANCO,
        None
    )


def test_obter_sala_converte_erro_mysql(monkeypatch):
    monkeypatch.setattr(
        salas_controller.sala_service,
        "buscar_sala_por_id",
        _falha_banco
    )

    resultado = salas_controller.obter_sala(1)

    assert resultado == (
        False,
        MENSAGEM_ERRO_BANCO,
        None
    )
