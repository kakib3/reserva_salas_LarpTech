"""Cada controller deve devolver (False, mensagem_amigavel, None) quando o service
levanta ErroDeDados. Estes testes importam os controllers reais do projeto."""
import pytest

from app.utils.excecoes import ErroDeDados
from app.controllers import reservas_controller, salas_controller, usuarios_controller

MSG = "Os dados estão ilegíveis no momento."


def _falha(*args, **kwargs):
    raise ErroDeDados(MSG)


@pytest.mark.parametrize(
    "controller, funcao_service, chamada",
    [
        (reservas_controller, "criar_reserva", lambda c: c.reservar_sala(1, "S1", None, None, None)),
        (reservas_controller, "cancelar_reserva", lambda c: c.cancelar_reserva("R1", 1)),
        (reservas_controller, "alterar_reserva", lambda c: c.alterar_reserva("R1", 1, "S1", None, None, None)),
        (reservas_controller, "aprovar_reserva", lambda c: c.aprovar_reserva("R1", 1)),
        (reservas_controller, "negar_reserva", lambda c: c.negar_reserva("R1", 1)),
        (usuarios_controller, "autenticar_usuario", lambda c: c.fazer_login("a@b.c", "x")),
    ],
)
def test_controller_converte_erro_de_dados(monkeypatch, controller, funcao_service, chamada):
    service = getattr(controller, "reservas_service", None) or getattr(controller, "usuarios_service")
    monkeypatch.setattr(service, funcao_service, _falha)
    assert chamada(controller) == (False, MSG, None)


def test_ocultar_sala_converte_erro_de_dados(monkeypatch):
    monkeypatch.setattr(salas_controller.sala_service, "ocultar_sala", _falha)
    assert salas_controller.ocultar_sala("S1", 1) == (False, MSG, None)
    