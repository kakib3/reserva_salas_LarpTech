from datetime import date, datetime, timedelta, timezone

from app.utils import relogio
from app.utils.relogio import FUSO, agora, hoje


class _DatetimeFalso(datetime):
    """Substitui datetime dentro de relogio.py: 'agora' real = 17/11/2026 03:30 UTC."""

    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 11, 17, 3, 30, tzinfo=timezone.utc).astimezone(tz)


# Fuso

def test_fuso_e_porto_velho():
    assert FUSO.key == "America/Porto_Velho"


def test_fuso_e_utc_menos_4_o_ano_todo():
    # O Brasil não usa horário de verão desde 2019.
    verao_do_norte = datetime(2026, 1, 15, 12, 0, tzinfo=FUSO)
    inverno_do_norte = datetime(2026, 7, 15, 12, 0, tzinfo=FUSO)

    assert verao_do_norte.utcoffset() == timedelta(hours=-4)
    assert inverno_do_norte.utcoffset() == timedelta(hours=-4)


# agora()

def test_agora_devolve_datetime_com_fuso():
    momento = agora()

    assert isinstance(momento, datetime)
    assert momento.tzinfo is not None
    assert momento.utcoffset() == timedelta(hours=-4)


def test_agora_esta_perto_do_instante_real():
    diferenca = abs(agora() - datetime.now(timezone.utc))

    assert diferenca < timedelta(seconds=5)


def test_agora_usa_o_fuso_de_porto_velho(monkeypatch):
    monkeypatch.setattr(relogio, "datetime", _DatetimeFalso)

    momento = agora()

    assert momento.tzinfo is FUSO
    assert (momento.hour, momento.minute) == (23, 30)


# hoje()

def test_hoje_devolve_date_e_nao_datetime():
    resultado = hoje()

    assert type(resultado) is date


def test_hoje_e_a_data_de_agora(monkeypatch):
    fixo = datetime(2026, 11, 16, 14, 30, tzinfo=FUSO)
    monkeypatch.setattr(relogio, "agora", lambda: fixo)

    assert hoje() == date(2026, 11, 16)


def test_hoje_usa_o_dia_local_e_nao_o_do_servidor_em_utc(monkeypatch):
    # Servidor em UTC já está em 17/11 às 03:30, mas em Porto Velho ainda é 16/11 às 23:30.
    monkeypatch.setattr(relogio, "datetime", _DatetimeFalso)

    assert hoje() == date(2026, 11, 16)
    assert hoje() != date(2026, 11, 17)