from datetime import date, datetime, time

import pytest

from app.models.reserva import Reserva
from app.services.reservas_service import _validar_reserva
from app.utils.relogio import FUSO

# Segunda-feira, 16/11/2026, 14:30:20 em Porto Velho.
MOMENTO = datetime(2026, 11, 16, 14, 30, 20, tzinfo=FUSO)

ONTEM = date(2026, 11, 15)       # domingo
HOJE = date(2026, 11, 16)        # segunda
AMANHA = date(2026, 11, 17)      # terça
DOMINGO_FUTURO = date(2026, 11, 22)


@pytest.fixture
def relogio_fixo(monkeypatch):
    """Congela o 'agora' usado pelo model Reserva."""
    monkeypatch.setattr("app.models.reserva.agora", lambda: MOMENTO)


def _reserva(data, inicio=time(15, 0), fim=time(16, 0)):
    return Reserva(None, 1, 1, data, inicio, fim, None, None)


# validar_nao_passado

def test_data_de_ontem_e_rejeitada(relogio_fixo):
    with pytest.raises(ValueError, match="passado"):
        _reserva(ONTEM).validar_nao_passado()


def test_data_muito_antiga_e_rejeitada(relogio_fixo):
    with pytest.raises(ValueError, match="passado"):
        _reserva(date(2026, 6, 15)).validar_nao_passado()


def test_hoje_com_inicio_ja_passado_e_rejeitado(relogio_fixo):
    with pytest.raises(ValueError, match="já passou"):
        _reserva(HOJE, time(9, 0), time(10, 0)).validar_nao_passado()


def test_hoje_com_inicio_futuro_passa(relogio_fixo):
    _reserva(HOJE, time(15, 0), time(16, 0)).validar_nao_passado()


def test_amanha_com_horario_anterior_ao_atual_passa(relogio_fixo):
    _reserva(AMANHA, time(8, 0), time(9, 0)).validar_nao_passado()


def test_inicio_exatamente_igual_ao_instante_atual_passa(relogio_fixo):
    # Documenta o operador '<': só rejeita o que é estritamente anterior.
    _reserva(HOJE, time(14, 30, 20), time(16, 0)).validar_nao_passado()


def test_inicio_no_minuto_atual_ja_passou_por_causa_dos_segundos(relogio_fixo):
    # São 14:30:20, então 14:30:00 já passou. Se a regra mudar para comparar
    # só até o minuto, este teste deve ser atualizado de propósito.
    with pytest.raises(ValueError, match="já passou"):
        _reserva(HOJE, time(14, 30), time(16, 0)).validar_nao_passado()


def test_um_segundo_antes_do_instante_atual_e_rejeitado(relogio_fixo):
    with pytest.raises(ValueError, match="já passou"):
        _reserva(HOJE, time(14, 30, 19), time(16, 0)).validar_nao_passado()


def test_perto_da_meia_noite_usa_o_dia_local(monkeypatch):
    # 23:30 em Porto Velho (03:30 UTC do dia seguinte): "hoje" continua sendo dia 16.
    tarde = datetime(2026, 11, 16, 23, 30, tzinfo=FUSO)
    monkeypatch.setattr("app.models.reserva.agora", lambda: tarde)

    _reserva(HOJE, time(23, 45), time(23, 59)).validar_nao_passado()

    with pytest.raises(ValueError, match="já passou"):
        _reserva(HOJE, time(23, 0), time(23, 59)).validar_nao_passado()

    _reserva(AMANHA, time(8, 0), time(9, 0)).validar_nao_passado()


def test_mensagens_de_erro_sao_diferentes_para_data_e_horario(relogio_fixo):
    with pytest.raises(ValueError) as erro_data:
        _reserva(ONTEM).validar_nao_passado()

    with pytest.raises(ValueError) as erro_hora:
        _reserva(HOJE, time(9, 0), time(10, 0)).validar_nao_passado()

    assert str(erro_data.value) != str(erro_hora.value)


# _validar_reserva (service): a nova validação está ligada e não mascara as outras

def test_validar_reserva_aceita_reserva_futura_valida(relogio_fixo):
    _validar_reserva(_reserva(AMANHA, time(19, 0), time(21, 0)))


def test_validar_reserva_aceita_hoje_com_horario_futuro(relogio_fixo):
    _validar_reserva(_reserva(HOJE, time(15, 0), time(17, 0)))


def test_validar_reserva_rejeita_data_passada(relogio_fixo):
    # 12/11/2026 é quinta-feira, então só a regra de passado pode barrar.
    with pytest.raises(ValueError, match="passado"):
        _validar_reserva(_reserva(date(2026, 11, 12), time(19, 0), time(21, 0)))


def test_validar_reserva_rejeita_hoje_com_horario_passado(relogio_fixo):
    with pytest.raises(ValueError, match="já passou"):
        _validar_reserva(_reserva(HOJE, time(8, 0), time(9, 0)))


def test_validar_reserva_continua_rejeitando_domingo_futuro(relogio_fixo):
    with pytest.raises(ValueError, match="dias úteis"):
        _validar_reserva(_reserva(DOMINGO_FUTURO, time(19, 0), time(21, 0)))


def test_validar_reserva_continua_rejeitando_duracao_invalida(relogio_fixo):
    with pytest.raises(ValueError, match="pelo menos"):
        _validar_reserva(_reserva(AMANHA, time(19, 0), time(19, 20)))

    with pytest.raises(ValueError, match="4 horas"):
        _validar_reserva(_reserva(AMANHA, time(17, 0), time(22, 0)))


def test_validar_reserva_continua_rejeitando_fora_do_funcionamento(relogio_fixo):
    with pytest.raises(ValueError, match="07:00"):
        _validar_reserva(_reserva(AMANHA, time(6, 0), time(8, 0)))


def test_hora_com_tipo_errado_gera_valueerror_e_nao_typeerror(relogio_fixo):
    # As validações anteriores barram antes da comparação de passado.
    with pytest.raises(ValueError, match="time"):
        _validar_reserva(_reserva(HOJE, "15:00", "16:00"))


def test_data_com_tipo_errado_gera_valueerror_e_nao_typeerror(relogio_fixo):
    with pytest.raises(ValueError, match="date"):
        _validar_reserva(_reserva("2026-11-17", time(19, 0), time(21, 0)))