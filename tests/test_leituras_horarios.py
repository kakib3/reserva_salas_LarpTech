from datetime import date, time, timedelta

import pytest

from app.services import reservas_service, sala_service


# Banco falso: o MySQL devolve colunas TIME como timedelta

class CursorFalso:
    def __init__(self, fetchone=None, fetchall=None):
        self._fetchone = fetchone
        self._fetchall = fetchall if fetchall is not None else []
        self.consultas = []
        self.fechado = False

    def execute(self, sql, params=None):
        self.consultas.append((sql, params))

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return self._fetchall

    def close(self):
        self.fechado = True


class ConexaoFalsa:
    def __init__(self, cursor):
        self.cursor_falso = cursor
        self.fechada = False

    def cursor(self, *args, **kwargs):
        return self.cursor_falso

    def close(self):
        self.fechada = True


def _fixar_banco(monkeypatch, modulo, *roteiros):
    """Cada conectar_banco() do módulo devolve a próxima conexão falsa, na ordem dos roteiros."""
    conexoes = [ConexaoFalsa(CursorFalso(**roteiro)) for roteiro in roteiros]
    fila = iter(conexoes)
    monkeypatch.setattr(modulo, "conectar_banco", lambda: next(fila))
    return conexoes


def _linha_reserva(**extra):
    linha = {
        "id_reserva": 1,
        "id_usuario": 1,
        "id_sala": 1,
        "nome_sala": "Sala01",
        "data_reserva": date(2026, 11, 17),
        "hora_inicio": timedelta(hours=19),
        "hora_fim": timedelta(hours=21),
        "status_reserva": "Confirmada",
    }
    linha.update(extra)
    return linha

# reservas_service: consultas que alimentam as telas

def test_consultar_reservas_usuario_devolve_horarios_como_time(monkeypatch):
    conexoes = _fixar_banco(monkeypatch, reservas_service, {
        "fetchall": [
            _linha_reserva(id_reserva=1, hora_inicio=timedelta(hours=8), hora_fim=timedelta(hours=9, minutes=30)),
            _linha_reserva(id_reserva=2, hora_inicio=timedelta(hours=19), hora_fim=timedelta(hours=21)),
        ]
    })

    resultado = reservas_service.consultar_reservas_usuario(1)

    assert resultado[0]["hora_inicio"] == time(8, 0)
    assert resultado[0]["hora_fim"] == time(9, 30)
    assert resultado[1]["hora_inicio"] == time(19, 0)
    assert resultado[1]["hora_fim"] == time(21, 0)
    assert all(isinstance(r["hora_inicio"], time) for r in resultado)
    assert all(c.fechada and c.cursor_falso.fechado for c in conexoes)


def test_consultar_reservas_usuario_marca_pode_alterar_pelo_status(monkeypatch):
    _fixar_banco(monkeypatch, reservas_service, {
        "fetchall": [
            _linha_reserva(id_reserva=1, status_reserva="Confirmada"),
            _linha_reserva(id_reserva=2, status_reserva="Pendente"),
            _linha_reserva(id_reserva=3, status_reserva="Cancelada"),
        ]
    })

    resultado = reservas_service.consultar_reservas_usuario(1)

    assert [r["pode_alterar"] for r in resultado] == [True, True, False]


def test_consultar_reservas_usuario_sem_reservas_devolve_lista_vazia(monkeypatch):
    _fixar_banco(monkeypatch, reservas_service, {"fetchall": []})

    assert reservas_service.consultar_reservas_usuario(1) == []


def test_consultar_reservas_pendentes_devolve_horarios_como_time(monkeypatch):
    monkeypatch.setattr(reservas_service.usuarios_service, "exigir_admin", lambda id_solicitante: None)
    conexoes = _fixar_banco(monkeypatch, reservas_service, {
        "fetchall": [
            _linha_reserva(nome_usuario="Joao", papel="Aluno", status_reserva="Pendente"),
        ]
    })

    resultado = reservas_service.consultar_reservas_pendentes(5)

    assert resultado[0]["hora_inicio"] == time(19, 0)
    assert resultado[0]["hora_fim"] == time(21, 0)
    assert conexoes[0].fechada


def test_consultar_reservas_pendentes_sem_permissao_nao_abre_conexao(monkeypatch):
    def negar(id_solicitante):
        raise PermissionError("Ação não permitida.")

    chamadas = []
    monkeypatch.setattr(reservas_service.usuarios_service, "exigir_admin", negar)
    monkeypatch.setattr(reservas_service, "conectar_banco", lambda: chamadas.append(1))

    with pytest.raises(PermissionError):
        reservas_service.consultar_reservas_pendentes(1)

    assert chamadas == []


def test_consultar_proxima_reserva_devolve_horarios_como_time(monkeypatch):
    conexoes = _fixar_banco(monkeypatch, reservas_service, {"fetchone": _linha_reserva()})

    resultado = reservas_service.consultar_proxima_reserva(1, date(2026, 11, 16))

    assert resultado["hora_inicio"] == time(19, 0)
    assert resultado["hora_fim"] == time(21, 0)
    assert conexoes[0].fechada


def test_consultar_proxima_reserva_envia_a_data_atual_na_consulta(monkeypatch):
    conexoes = _fixar_banco(monkeypatch, reservas_service, {"fetchone": None})

    reservas_service.consultar_proxima_reserva(7, date(2026, 11, 16))

    _, parametros = conexoes[0].cursor_falso.consultas[0]
    assert parametros[0] == 7
    assert parametros[-1] == date(2026, 11, 16)


def test_consultar_proxima_reserva_sem_resultado_devolve_none(monkeypatch):
    conexoes = _fixar_banco(monkeypatch, reservas_service, {"fetchone": None})

    assert reservas_service.consultar_proxima_reserva(1, date(2026, 11, 16)) is None
    assert conexoes[0].fechada

# sala_service.consultar_disponibilidade

def _disponibilidade(monkeypatch, status_sala, reservas):
    monkeypatch.setattr(sala_service.salas_ocultas, "esta_oculta", lambda id_sala: False)

    sala = {"id_sala": 1, "nome": "Sala01", "status_sala": status_sala}
    conexoes = _fixar_banco(
        monkeypatch, sala_service,
        {"fetchone": sala},          # buscar_sala_por_id
        {"fetchall": reservas},      # reservas do dia
    )

    resultado = sala_service.consultar_disponibilidade(1, date(2026, 11, 17), 1)
    return resultado, conexoes


def _reserva_do_dia(inicio, fim):
    return {
        "id_reserva": 1,
        "id_usuario": 1,
        "nome_usuario": "Joao",
        "data_reserva": date(2026, 11, 17),
        "hora_inicio": inicio,
        "hora_fim": fim,
        "status_reserva": "Confirmada",
    }


def test_disponibilidade_converte_horarios_das_reservas_para_time(monkeypatch):
    resultado, conexoes = _disponibilidade(monkeypatch, "Disponivel", [
        _reserva_do_dia(timedelta(hours=19), timedelta(hours=21)),
    ])

    assert resultado["reservas"][0]["hora_inicio"] == time(19, 0)
    assert resultado["reservas"][0]["hora_fim"] == time(21, 0)
    assert all(c.fechada for c in conexoes)


def test_disponibilidade_calcula_horarios_livres_sem_typeerror(monkeypatch):
    resultado, _ = _disponibilidade(monkeypatch, "Disponivel", [
        _reserva_do_dia(timedelta(hours=19), timedelta(hours=21)),
    ])

    assert resultado["reservavel"] is True
    assert resultado["horarios_livres"] == [
        (time(7, 0), time(19, 0)),
        (time(21, 0), time(22, 0)),
    ]


def test_disponibilidade_sem_reservas_libera_o_expediente_inteiro(monkeypatch):
    resultado, _ = _disponibilidade(monkeypatch, "Disponivel", [])

    assert resultado["horarios_livres"] == [(time(7, 0), time(22, 0))]


def test_disponibilidade_com_varias_reservas(monkeypatch):
    resultado, _ = _disponibilidade(monkeypatch, "Disponivel", [
        _reserva_do_dia(timedelta(hours=8), timedelta(hours=9)),
        _reserva_do_dia(timedelta(hours=10), timedelta(hours=12)),
    ])

    assert resultado["horarios_livres"] == [
        (time(7, 0), time(8, 0)),
        (time(9, 0), time(10, 0)),
        (time(12, 0), time(22, 0)),
    ]


def test_disponibilidade_ignora_intervalo_menor_que_30_minutos(monkeypatch):
    resultado, _ = _disponibilidade(monkeypatch, "Disponivel", [
        _reserva_do_dia(timedelta(hours=8), timedelta(hours=9)),
        _reserva_do_dia(timedelta(hours=9, minutes=20), timedelta(hours=10)),
    ])

    assert (time(9, 0), time(9, 20)) not in resultado["horarios_livres"]
    assert resultado["horarios_livres"] == [
        (time(7, 0), time(8, 0)),
        (time(10, 0), time(22, 0)),
    ]


def test_disponibilidade_de_sala_em_manutencao_nao_tem_horarios_livres(monkeypatch):
    resultado, _ = _disponibilidade(monkeypatch, "Manutencao", [])

    assert resultado["reservavel"] is False
    assert resultado["horarios_livres"] == []


def test_disponibilidade_de_sala_inexistente_devolve_none(monkeypatch):
    conexoes = _fixar_banco(monkeypatch, sala_service, {"fetchone": None})

    assert sala_service.consultar_disponibilidade(999, date(2026, 11, 17), 1) is None
    assert conexoes[0].fechada
