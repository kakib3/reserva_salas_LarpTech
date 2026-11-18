"""Datas de teste calculadas a partir do relógio do app, nunca fixas.

Datas fixas (ex.: date(2026, 11, 16)) viram "passado" com o tempo e quebram os testes
que passam pela validação de reservas.
"""
from datetime import timedelta

from app.utils.relogio import hoje


def proximo_dia_da_semana(dia, a_partir_de_dias=7):
    """Primeiro dia da semana `dia` (0=segunda ... 6=domingo) pelo menos N dias à frente."""
    data = hoje() + timedelta(days=a_partir_de_dias)
    while data.weekday() != dia:
        data += timedelta(days=1)
    return data


SEGUNDA_FUTURA = proximo_dia_da_semana(0)
DOMINGO_FUTURO = proximo_dia_da_semana(6)
