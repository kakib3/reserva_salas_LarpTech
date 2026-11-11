
from datetime import date, time
import pytest

from app.models.constantes import StatusReserva
from app.services import reservas_service


def criar_dados_reserva():
    return {
        "id_usuario": 10,
        "id_sala": 5,
        "data_reserva": date(2026, 11, 16),
        "hora_inicio": time(14, 0),
        "hora_fim": time(16, 0),
        "status_reserva": StatusReserva.PENDENTE,
        "criado_em": date(2026, 11, 10),
    }


class FakeCursor:
    def __init__(self, dados=None):
        self.dados = dados
        self.sql = None
        self.valores = None

    def execute(self, sql, valores):
        self.sql = sql
        self.valores = valores

    def fetchone(self):
        return self.dados

    def close(self):
        pass


class FakeConexao:
    def __init__(self, dados=None):
        self.cursor_fake = FakeCursor(dados)
        self.commitado = False
        self.fechado = False

    def cursor(self, **kwargs):
        return self.cursor_fake

    def commit(self):
        self.commitado = True

    def close(self):
        self.fechado = True


def test_aprovar_reserva_notifica_usuario(monkeypatch):
    conexao_consulta = FakeConexao(criar_dados_reserva())
    conexao_update = FakeConexao()

    conexoes = iter([conexao_consulta, conexao_update])

    monkeypatch.setattr(
        reservas_service.usuarios_service,
        "checar_admin",
        lambda id_usuario: True
    )
    monkeypatch.setattr(
        reservas_service,
        "conectar_banco",
        lambda: next(conexoes)
    )
    monkeypatch.setattr(
        reservas_service,
        "verificar_sala_disponivel",
        lambda id_sala: True
    )

    chamadas = []

    def simular_notificacao(reserva):
        assert conexao_update.commitado
        assert conexao_update.fechado
        chamadas.append(reserva)
        return True

    monkeypatch.setattr(
        reservas_service.notificacoes_service,
        "notificar_reserva_aprovada",
        simular_notificacao
    )

    resultado = reservas_service.aprovar_reserva(1, 99)

    assert resultado is True
    assert len(chamadas) == 1
    assert chamadas[0].id == 1
    assert chamadas[0].status == StatusReserva.CONFIRMADA


def test_negar_reserva_notifica_usuario(monkeypatch):
    conexao = FakeConexao(criar_dados_reserva())

    monkeypatch.setattr(
        reservas_service.usuarios_service,
        "checar_admin",
        lambda id_usuario: True
    )
    monkeypatch.setattr(
        reservas_service,
        "conectar_banco",
        lambda: conexao
    )

    chamadas = []

    def simular_notificacao(reserva):
        assert conexao.commitado
        assert conexao.fechado
        chamadas.append(reserva)
        return True

    monkeypatch.setattr(
        reservas_service.notificacoes_service,
        "notificar_reserva_recusada",
        simular_notificacao
    )

    resultado = reservas_service.negar_reserva(1, 99)

    assert resultado is True
    assert len(chamadas) == 1
    assert chamadas[0].id == 1
    assert chamadas[0].status == StatusReserva.CANCELADA



@pytest.mark.parametrize(
    "operacao",
    ["aprovar_reserva", "negar_reserva"]
)
def test_decisao_admin_nao_depende_do_envio_email(
    monkeypatch,
    operacao
):
    conexao_consulta = FakeConexao(criar_dados_reserva())
    conexao_update = FakeConexao()

    if operacao == "aprovar_reserva":
        conexoes = iter([conexao_consulta, conexao_update])
        conexao_commit = conexao_update
    else:
        conexoes = iter([conexao_consulta])
        conexao_commit = conexao_consulta

    monkeypatch.setattr(
        reservas_service.usuarios_service,
        "checar_admin",
        lambda id_usuario: True
    )
    monkeypatch.setattr(
        reservas_service,
        "conectar_banco",
        lambda: next(conexoes)
    )
    monkeypatch.setattr(
        reservas_service,
        "verificar_sala_disponivel",
        lambda id_sala: True
    )

    def falhar_notificacao(reserva):
        raise RuntimeError("Falha simulada no e-mail")

    monkeypatch.setattr(
        reservas_service.notificacoes_service,
        "notificar_reserva_aprovada",
        falhar_notificacao
    )
    monkeypatch.setattr(
        reservas_service.notificacoes_service,
        "notificar_reserva_recusada",
        falhar_notificacao
    )

    resultado = getattr(
        reservas_service, operacao
    )(1, 99)

    assert resultado is True
    assert conexao_commit.commitado
    assert conexao_commit.fechado