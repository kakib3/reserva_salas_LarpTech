from datetime import date, datetime, time

import pytest

from app.models.reserva import Reserva
from app.utils.horarios import horarios_padrao
from app.utils.relogio import FUSO

HOJE = date(2026, 11, 16)      # segunda-feira
AMANHA = date(2026, 11, 17)


def _fixar_relogio(monkeypatch, hora, minuto=0):
    """Congela agora() e hoje() dentro de app.utils.horarios em 16/11/2026 hora:minuto."""
    momento = datetime(2026, 11, 16, hora, minuto, tzinfo=FUSO)
    monkeypatch.setattr("app.utils.horarios.agora", lambda: momento)
    monkeypatch.setattr("app.utils.horarios.hoje", lambda: momento.date())

# Datas que não são hoje: padrão fixo

def test_data_futura_usa_o_padrao_das_8_as_9(monkeypatch):
    _fixar_relogio(monkeypatch, 10, 20)

    assert horarios_padrao(AMANHA) == (time(8, 0), time(9, 0))


def test_data_futura_ignora_a_hora_atual_mesmo_a_noite(monkeypatch):
    _fixar_relogio(monkeypatch, 23, 30)

    assert horarios_padrao(AMANHA) == (time(8, 0), time(9, 0))

# Hoje: próxima hora cheia

def test_hoje_as_10h20_sugere_11h_as_12h(monkeypatch):
    _fixar_relogio(monkeypatch, 10, 20)

    assert horarios_padrao(HOJE) == (time(11, 0), time(12, 0))


def test_hoje_exatamente_em_hora_cheia_sugere_a_hora_seguinte(monkeypatch):
    _fixar_relogio(monkeypatch, 14, 0)

    assert horarios_padrao(HOJE) == (time(15, 0), time(16, 0))


def test_hoje_de_madrugada_respeita_a_abertura_das_7h(monkeypatch):
    for hora, minuto in [(0, 10), (5, 0), (5, 59), (6, 30)]:
        _fixar_relogio(monkeypatch, hora, minuto)

        assert horarios_padrao(HOJE) == (time(7, 0), time(8, 0)), (hora, minuto)

# Hoje: fim do expediente

def test_hoje_as_20h59_sugere_o_ultimo_horario_valido(monkeypatch):
    _fixar_relogio(monkeypatch, 20, 59)

    assert horarios_padrao(HOJE) == (time(21, 0), time(22, 0))


def test_hoje_as_21h_nao_ha_mais_horario(monkeypatch):
    _fixar_relogio(monkeypatch, 21, 0)

    assert horarios_padrao(HOJE) is None


def test_hoje_as_23h30_nao_ha_mais_horario_e_nao_volta_para_as_7h(monkeypatch):
    # Somar timedelta(hours=1) a 23:30 viraria meia-noite e sugeriria 07:00 de hoje.
    _fixar_relogio(monkeypatch, 23, 30)

    assert horarios_padrao(HOJE) is None

# Propriedades que valem para qualquer hora do dia

@pytest.mark.parametrize("hora", range(24))
def test_sugestao_de_hoje_e_sempre_futura_e_valida(monkeypatch, hora):
    _fixar_relogio(monkeypatch, hora, 59)

    resultado = horarios_padrao(HOJE)

    if resultado is None:
        assert hora >= 21
        return

    inicio, fim = resultado

    assert isinstance(inicio, time) and isinstance(fim, time)
    assert inicio > time(hora, 59)
    assert fim.hour - inicio.hour == 1

    # Passa nas validações do próprio model Reserva (horário, duração e funcionamento).
    reserva = Reserva(None, 1, 1, HOJE, inicio, fim, None, None)
    reserva.validar_horario()
    reserva.validar_intervalo()
    reserva.validar_horario_funcionamento()


@pytest.mark.parametrize("hora", range(24))
def test_sugestao_de_data_futura_e_sempre_valida(monkeypatch, hora):
    _fixar_relogio(monkeypatch, hora, 0)

    inicio, fim = horarios_padrao(AMANHA)

    reserva = Reserva(None, 1, 1, AMANHA, inicio, fim, None, None)
    reserva.validar_horario()
    reserva.validar_intervalo()
    reserva.validar_horario_funcionamento()