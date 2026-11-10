
from datetime import date, time
from types import SimpleNamespace

import pytest

from app.messaging import notificacoes_service as notificacoes


def criar_reserva():
    return SimpleNamespace(
        id=1,
        usuario_id=10,
        sala_id=5,
        data=date(2026, 11, 15),
        hora_inicio=time(14, 0),
        hora_fim=time(16, 0),
    )


def test_enviar_notificacao_com_sucesso(monkeypatch):
    usuario = SimpleNamespace(email="professor@email.com")

    monkeypatch.setattr(
        notificacoes.usuarios_service,
        "buscar_usuario_por_id",
        lambda id_usuario: usuario
    )

    monkeypatch.setattr(
        notificacoes,
        "enviar_email",
        lambda **kwargs: True
    )

    resultado = notificacoes.enviar_notificacao(
        10,
        "Teste",
        "Mensagem de teste"
    )

    assert resultado is True


def test_enviar_notificacao_usuario_inexistente(monkeypatch):
    monkeypatch.setattr(
        notificacoes.usuarios_service,
        "buscar_usuario_por_id",
        lambda id_usuario: None
    )

    resultado = notificacoes.enviar_notificacao(
        999,
        "Teste",
        "Mensagem de teste"
    )

    assert resultado is False


def test_enviar_notificacao_usuario_sem_email(monkeypatch):
    usuario = SimpleNamespace(email=None)

    monkeypatch.setattr(
        notificacoes.usuarios_service,
        "buscar_usuario_por_id",
        lambda id_usuario: usuario
    )

    resultado = notificacoes.enviar_notificacao(
        10,
        "Teste",
        "Mensagem de teste"
    )

    assert resultado is False


@pytest.mark.parametrize(
    "funcao, assunto, situacao",
    [
        (
            notificacoes.notificar_reserva_confirmada,
            "Reserva confirmada - LarpTech",
            "Confirmada"
        ),
        (
            notificacoes.notificar_reserva_pendente,
            "Solicitação de reserva recebida - LarpTech",
            "Pendente de aprovação"
        ),
        (
            notificacoes.notificar_reserva_aprovada,
            "Reserva aprovada - LarpTech",
            "Aprovada"
        ),
        (
            notificacoes.notificar_reserva_recusada,
            "Reserva recusada - LarpTech",
            "Recusada"
        ),
    ]
)
def test_notificacoes_de_reserva(
    monkeypatch,
    funcao,
    assunto,
    situacao
):
    reserva = criar_reserva()

    sala = SimpleNamespace(
        nome="Laboratório 01",
        predio="Bloco A",
        andar="2º"
    )

    chamada = {}

    monkeypatch.setattr(
        notificacoes.sala_service,
        "buscar_sala_por_id",
        lambda id_sala: sala
    )

    def simular_envio(id_usuario, assunto, corpo):
        chamada["id_usuario"] = id_usuario
        chamada["assunto"] = assunto
        chamada["corpo"] = corpo
        return True

    monkeypatch.setattr(
        notificacoes,
        "enviar_notificacao",
        simular_envio
    )

    resultado = funcao(reserva)

    assert resultado is True
    assert chamada["id_usuario"] == 10
    assert chamada["assunto"] == assunto
    assert situacao in chamada["corpo"]
    assert "Laboratório 01" in chamada["corpo"]
    assert "15/11/2026" in chamada["corpo"]
    assert "14:00 às 16:00" in chamada["corpo"]


def test_notificacao_sala_inexistente(monkeypatch):
    reserva = criar_reserva()

    monkeypatch.setattr(
        notificacoes.sala_service,
        "buscar_sala_por_id",
        lambda id_sala: None
    )

    resultado = notificacoes.notificar_reserva_confirmada(reserva)

    assert resultado is False