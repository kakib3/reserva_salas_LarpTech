from datetime import date, time

import pytest

from app.models.constantes import StatusReserva
from app.services import reservas_service


class FakeCursor:
    lastrowid = 123

    def execute(self, sql, valores):
        self.sql = sql
        self.valores = valores

    def close(self):
        pass


class FakeConexao:
    def __init__(self):
        self.cursor_fake = FakeCursor()
        self.commitado = False
        self.fechado = False

    def cursor(self):
        return self.cursor_fake

    def commit(self):
        self.commitado = True

    def close(self):
        self.fechado = True


@pytest.fixture
def preparar_criacao(monkeypatch):
    conexao = FakeConexao()

    monkeypatch.setattr(
        reservas_service.usuarios_service,
        "checar_usuario_ativo",
        lambda id_usuario: True
    )
    monkeypatch.setattr(
        reservas_service,
        "verificar_sala_disponivel",
        lambda id_sala: True
    )
    monkeypatch.setattr(
        reservas_service,
        "verificar_conflito_horario",
        lambda *args, **kwargs: False
    )
    monkeypatch.setattr(
        reservas_service,
        "_definir_status_reserva",
        lambda id_sala: StatusReserva.CONFIRMADA
    )
    monkeypatch.setattr(
        reservas_service,
        "conectar_banco",
        lambda: conexao
    )

    return conexao


@pytest.mark.parametrize(
    "status, notificador_esperado, notificador_nao_esperado",
    [
        (
            StatusReserva.CONFIRMADA,
            "notificar_reserva_confirmada",
            "notificar_reserva_pendente"
        ),
        (
            StatusReserva.PENDENTE,
            "notificar_reserva_pendente",
            "notificar_reserva_confirmada"
        ),
    ]
)
def test_criar_reserva_dispara_notificacao(
    monkeypatch,
    preparar_criacao,
    status,
    notificador_esperado,
    notificador_nao_esperado
):
    conexao = preparar_criacao
    chamadas = []

    monkeypatch.setattr(
        reservas_service,
        "_definir_status_reserva",
        lambda id_sala: status
    )

    def simular_notificacao(reserva):
        assert conexao.commitado is True
        assert conexao.fechado is True
        chamadas.append(reserva)
        return True

    monkeypatch.setattr(
        reservas_service.notificacoes_service,
        notificador_esperado,
        simular_notificacao
    )

    monkeypatch.setattr(
        reservas_service.notificacoes_service,
        notificador_nao_esperado,
        lambda reserva: pytest.fail("Notificador incorreto foi chamado.")
    )

    resultado = reservas_service.criar_reserva(
        id_usuario=10,
        id_sala=5,
        data=date(2026, 11, 16),
        hora_inicio=time(14, 0),
        hora_fim=time(16, 0)
    )

    assert resultado is not False
    assert resultado.id == 123
    assert resultado.status == status
    assert len(chamadas) == 1
    assert chamadas[0] is resultado


@pytest.mark.parametrize("tipo_falha", ["retorno_false", "excecao"])
def test_falha_na_notificacao_nao_impede_criar_reserva(
    monkeypatch,
    preparar_criacao,
    tipo_falha
):
    def simular_falha(reserva):
        if tipo_falha == "excecao":
            raise RuntimeError("Falha simulada no envio")

        return False

    monkeypatch.setattr(
        reservas_service.notificacoes_service,
        "notificar_reserva_confirmada",
        simular_falha
    )

    resultado = reservas_service.criar_reserva(
        id_usuario=10,
        id_sala=5,
        data=date(2026, 11, 16),
        hora_inicio=time(14, 0),
        hora_fim=time(16, 0)
    )

    assert resultado is not False
    assert resultado.id == 123
    assert resultado.status == StatusReserva.CONFIRMADA
    assert preparar_criacao.commitado is True
    assert preparar_criacao.fechado is True