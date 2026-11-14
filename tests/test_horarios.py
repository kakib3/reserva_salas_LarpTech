from datetime import time, timedelta

import pytest

from app.utils.horarios import normalizar_horarios


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        (timedelta(hours=19), time(19, 0)),
        (timedelta(hours=7), time(7, 0)),
        (timedelta(hours=7, minutes=30), time(7, 30)),
        (timedelta(hours=7, minutes=30, seconds=15), time(7, 30, 15)),
        (timedelta(0), time(0, 0)),
        (timedelta(hours=23, minutes=59, seconds=59), time(23, 59, 59)),
    ],
)
def test_converte_timedelta_para_time(entrada, esperado):
    registro = {"hora_inicio": entrada}

    normalizar_horarios(registro)

    assert registro["hora_inicio"] == esperado
    assert isinstance(registro["hora_inicio"], time)

def test_converte_os_dois_campos_padrao():
    registro = {
        "hora_inicio": timedelta(hours=19),
        "hora_fim": timedelta(hours=21, minutes=45),
    }

    normalizar_horarios(registro)

    assert registro["hora_inicio"] == time(19, 0)
    assert registro["hora_fim"] == time(21, 45)

def test_timedelta_de_24h_ou_mais_cai_dentro_do_dia():
    registro = {
        "hora_inicio": timedelta(hours=24),
        "hora_fim": timedelta(hours=25, minutes=30),
    }

    normalizar_horarios(registro)

    assert registro["hora_inicio"] == time(0, 0)
    assert registro["hora_fim"] == time(1, 30)

def test_microssegundos_sao_descartados():
    registro = {"hora_inicio": timedelta(hours=7, microseconds=500000)}

    normalizar_horarios(registro)

    assert registro["hora_inicio"] == time(7, 0, 0)

def test_valor_que_ja_e_time_fica_intacto():
    original = time(19, 0)
    registro = {"hora_inicio": original}

    normalizar_horarios(registro)

    assert registro["hora_inicio"] is original

def test_valor_none_continua_none():
    registro = {"hora_inicio": None, "hora_fim": None}

    normalizar_horarios(registro)

    assert registro == {"hora_inicio": None, "hora_fim": None}

def test_campo_ausente_nao_e_criado_nem_quebra():
    registro = {"hora_inicio": timedelta(hours=8)}

    normalizar_horarios(registro)

    assert registro == {"hora_inicio": time(8, 0)}
    assert "hora_fim" not in registro

def test_registro_sem_campos_de_hora_e_aceito():
    registro = {"id_reserva": 1, "nome_sala": "Sala01"}

    normalizar_horarios(registro)

    assert registro == {"id_reserva": 1, "nome_sala": "Sala01"}

def test_registro_vazio_e_aceito():
    registro = {}

    normalizar_horarios(registro)

    assert registro == {}

def test_modifica_o_registro_no_lugar_e_retorna_none():
    registro = {"hora_inicio": timedelta(hours=8)}

    resultado = normalizar_horarios(registro)

    assert resultado is None
    assert registro["hora_inicio"] == time(8, 0)

def test_nao_mexe_nos_outros_campos():
    registro = {
        "id_reserva": 10,
        "nome_sala": "Lab01",
        "status_reserva": "Pendente",
        "hora_inicio": timedelta(hours=9),
        "hora_fim": timedelta(hours=10),
    }

    normalizar_horarios(registro)

    assert registro["id_reserva"] == 10
    assert registro["nome_sala"] == "Lab01"
    assert registro["status_reserva"] == "Pendente"

def test_campos_customizados_convertem_so_os_indicados():
    registro = {
        "hora_inicio": timedelta(hours=8),
        "hora_abertura": timedelta(hours=7),
    }

    normalizar_horarios(registro, campos=("hora_abertura",))

    assert registro["hora_abertura"] == time(7, 0)
    # o campo padrão não foi indicado, então continua como veio do driver
    assert registro["hora_inicio"] == timedelta(hours=8)

def test_campos_vazio_nao_converte_nada():
    registro = {"hora_inicio": timedelta(hours=8)}

    normalizar_horarios(registro, campos=())

    assert registro["hora_inicio"] == timedelta(hours=8)

def test_aplicado_em_lista_de_registros():
    reservas = [
        {"hora_inicio": timedelta(hours=8), "hora_fim": timedelta(hours=9)},
        {"hora_inicio": timedelta(hours=19), "hora_fim": timedelta(hours=21)},
    ]

    for reserva in reservas:
        normalizar_horarios(reserva)

    assert [r["hora_inicio"] for r in reservas] == [time(8, 0), time(19, 0)]
    assert [r["hora_fim"] for r in reservas] == [time(9, 0), time(21, 0)]
