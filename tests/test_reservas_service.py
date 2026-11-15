
from datetime import date, time, timedelta
from unittest.mock import Mock
from copy import deepcopy

import pytest

from app.models.constantes import (
    PapelUsuario,
    StatusReserva,
    StatusSala,
    TipoSala,
)
from app.services import reservas_service as service


# MOCKS DO BANCO DE DADOS

class MockCursor:
    def __init__(self, resultado=None, resultados=None, lastrowid=100):
        self.resultado = deepcopy(resultado)
        self.resultados = deepcopy(resultados) if resultados else []
        self.lastrowid = lastrowid
        self.executado = []
        self.fechado = False
        self.rowcount = 1

    def execute(self, sql, valores=None):
        self.executado.append((sql, valores))

    def fetchone(self):
        return self.resultado

    def fetchall(self):
        return self.resultados

    def close(self):
        self.fechado = True


class MockConexao:
    def __init__(self, resultado=None, resultados=None, lastrowid=100):
        self.mock_cursor = MockCursor(resultado, resultados, lastrowid)
        self.commit_chamado = False
        self.fechado = False

    def cursor(self, dictionary=False, **kwargs):
        return self.mock_cursor

    def commit(self):
        self.commit_chamado = True

    def close(self):
        self.fechado = True


def configurar_conexoes(monkeypatch, *conexoes):
    """Entrega as conexões na ordem em que o service solicitar."""
    fila = iter(conexoes)
    monkeypatch.setattr(service, "conectar_banco", lambda: next(fila))


def configurar_usuario_ativo(monkeypatch, ativo=True):
    monkeypatch.setattr(
        service.usuarios_service,
        "checar_usuario_ativo",
        lambda id_usuario: ativo,
    )


def configurar_admin(monkeypatch, admin=True):
    monkeypatch.setattr(
        service.usuarios_service,
        "checar_admin",
        lambda id_usuario: admin,
    )

# DADOS UTILIZADOS NOS TESTES

DATA = date(2026, 11, 16)
INICIO = time(19, 0)
FIM = time(21, 0)

RESERVA_PENDENTE = {
    "id_usuario": 10,
    "id_sala": 6,
    "data_reserva": DATA,
    "hora_inicio": INICIO,
    "hora_fim": FIM,
    "status_reserva": StatusReserva.PENDENTE,
}

RESERVA_CONFIRMADA = {
    "id_usuario": 10,
    "status_reserva": StatusReserva.CONFIRMADA,
}

# VERIFICAÇÃO DE DISPONIBILIDADE DA SALA

def test_sala_disponivel_retorna_true(monkeypatch):
    conexao = MockConexao(
        resultado={"status_sala": StatusSala.DISPONIVEL}
    )
    configurar_conexoes(monkeypatch, conexao)

    resultado = service.verificar_sala_disponivel(1)

    assert resultado is True
    assert conexao.mock_cursor.fechado
    assert conexao.fechado


def test_sala_em_manutencao_retorna_false(monkeypatch):
    conexao = MockConexao(
        resultado={"status_sala": StatusSala.MANUTENCAO}
    )
    configurar_conexoes(monkeypatch, conexao)

    assert service.verificar_sala_disponivel(1) is False


def test_sala_inexistente_retorna_false(monkeypatch):
    conexao = MockConexao(resultado=None)
    configurar_conexoes(monkeypatch, conexao)

    assert service.verificar_sala_disponivel(999) is False

# CONFLITOS DE HORÁRIO

def test_obter_conflitos_horario_retorna_resultados(monkeypatch):
    conflitos = [
        {"id_reserva": 5, "papel": PapelUsuario.ALUNO}
    ]
    conexao = MockConexao(resultados=conflitos)
    configurar_conexoes(monkeypatch, conexao)

    resultado = service.obter_conflitos_horario(
        2, DATA, INICIO, FIM
    )

    assert resultado == conflitos

    sql, valores = conexao.mock_cursor.executado[0]

    assert "r.id_sala = %s" in sql
    assert "r.data_reserva = %s" in sql
    assert "r.hora_inicio < %s" in sql
    assert "r.hora_fim > %s" in sql
    assert valores == (
        2,
        DATA,
        StatusReserva.CONFIRMADA,
        StatusReserva.PENDENTE,
        FIM,
        INICIO,
    )


def test_obter_conflitos_ignora_reserva_informada(monkeypatch):
    conexao = MockConexao(resultados=[])
    configurar_conexoes(monkeypatch, conexao)

    service.obter_conflitos_horario(
        2, DATA, INICIO, FIM, id_reserva_ignorar=15
    )

    sql, valores = conexao.mock_cursor.executado[0]

    assert "r.id_reserva != %s" in sql
    assert valores[-1] == 15


def test_verificar_conflito_retorna_true_quando_existe_conflito(monkeypatch):
    monkeypatch.setattr(
        service,
        "obter_conflitos_horario",
        lambda *args, **kwargs: [{"id_reserva": 1}],
    )

    assert service.verificar_conflito_horario(
        2, DATA, INICIO, FIM
    ) is True


def test_verificar_conflito_retorna_false_sem_conflitos(monkeypatch):
    monkeypatch.setattr(
        service,
        "obter_conflitos_horario",
        lambda *args, **kwargs: [],
    )

    assert service.verificar_conflito_horario(
        2, DATA, INICIO, FIM
    ) is False

# CRIAÇÃO DE RESERVAS

def preparar_criacao(monkeypatch, status=StatusReserva.CONFIRMADA):
    configurar_usuario_ativo(monkeypatch)

    monkeypatch.setattr(
        service,
        "verificar_sala_disponivel",
        lambda id_sala: True,
    )
    monkeypatch.setattr(
        service.salas_ocultas,
        "esta_oculta",
        lambda id_sala: False,
    )
    monkeypatch.setattr(
        service,
        "obter_conflitos_horario",
        lambda *args, **kwargs: [],
    )
    monkeypatch.setattr(
        service,
        "_papel_do_usuario",
        lambda id_usuario: PapelUsuario.ALUNO,
    )
    monkeypatch.setattr(
        service,
        "_definir_status_reserva",
        lambda id_sala: status,
    )


def test_criar_reserva_valida(monkeypatch):
    preparar_criacao(monkeypatch)

    conexao = MockConexao(lastrowid=42)
    configurar_conexoes(monkeypatch, conexao)

    resultado = service.criar_reserva(
        10, 2, DATA, INICIO, FIM
    )

    assert resultado is not False
    assert resultado.id == 42
    assert resultado.usuario_id == 10
    assert resultado.sala_id == 2
    assert resultado.status == StatusReserva.CONFIRMADA

    assert conexao.commit_chamado
    assert conexao.fechado

    sql, valores = conexao.mock_cursor.executado[0]

    assert "INSERT INTO reservas" in sql
    assert valores[0] == 10
    assert valores[1] == 2
    assert valores[5] == StatusReserva.CONFIRMADA


def test_criar_reserva_inicia_com_status_pendente_em_laboratorio(monkeypatch):
    preparar_criacao(monkeypatch, StatusReserva.PENDENTE)

    conexao = MockConexao(lastrowid=43)
    configurar_conexoes(monkeypatch, conexao)

    resultado = service.criar_reserva(
        10, 6, DATA, INICIO, FIM
    )

    assert resultado.status == StatusReserva.PENDENTE


def test_usuario_inativo_nao_cria_reserva(monkeypatch):
    preparar_criacao(monkeypatch)
    configurar_usuario_ativo(monkeypatch, ativo=False)

    resultado = service.criar_reserva(
        10, 2, DATA, INICIO, FIM
    )

    assert resultado is False


def test_sala_indisponivel_nao_recebe_reserva(monkeypatch):
    preparar_criacao(monkeypatch)

    monkeypatch.setattr(
        service,
        "verificar_sala_disponivel",
        lambda id_sala: False,
    )

    resultado = service.criar_reserva(
        10, 2, DATA, INICIO, FIM
    )

    assert resultado is False


def test_sala_oculta_nao_recebe_reserva(monkeypatch):
    preparar_criacao(monkeypatch)

    monkeypatch.setattr(
        service.salas_ocultas,
        "esta_oculta",
        lambda id_sala: True,
    )

    resultado = service.criar_reserva(
        10, 2, DATA, INICIO, FIM
    )

    assert resultado is False


def test_criar_reserva_com_conflito_e_rejeitada(monkeypatch):
    preparar_criacao(monkeypatch)

    monkeypatch.setattr(
        service,
        "obter_conflitos_horario",
        lambda *args, **kwargs: [
            {"id_reserva": 5, "papel": PapelUsuario.ALUNO}
        ],
    )

    resultado = service.criar_reserva(
        10, 2, DATA, INICIO, FIM
    )

    assert resultado is False


@pytest.mark.parametrize(
    "inicio,fim",
    [
        (time(19, 0), time(19, 20)),
        (time(17, 0), time(22, 0)),
        (time(19, 0), time(19, 0)),
        (time(6, 0), time(8, 0)),
    ],
)
def test_criar_reserva_com_horario_invalido_gera_erro(
    monkeypatch, inicio, fim
):
    preparar_criacao(monkeypatch)

    with pytest.raises(ValueError):
        service.criar_reserva(
            10, 2, DATA, inicio, fim
        )


def test_criar_reserva_no_domingo_gera_erro(monkeypatch):
    preparar_criacao(monkeypatch)

    domingo = date(2026, 11, 15)

    with pytest.raises(ValueError):
        service.criar_reserva(
            10, 2, domingo, INICIO, FIM
        )

# REGRA DE PRIORIDADE ENTRE USUÁRIOS

def test_sem_conflitos_todos_podem_reservar():
    permitido, ids = service._resolver_prioridade(
        PapelUsuario.ALUNO, []
    )

    assert permitido is True
    assert ids == []


def test_aluno_nao_pode_substituir_reserva_de_outro_usuario():
    conflitos = [
        {"id_reserva": 5, "papel": PapelUsuario.ALUNO}
    ]

    permitido, ids = service._resolver_prioridade(
        PapelUsuario.ALUNO, conflitos
    )

    assert permitido is False
    assert ids == []


def test_professor_pode_substituir_reserva_de_aluno():
    conflitos = [
        {"id_reserva": 5, "papel": PapelUsuario.ALUNO}
    ]

    permitido, ids = service._resolver_prioridade(
        PapelUsuario.PROFESSOR, conflitos
    )

    assert permitido is True
    assert ids == [5]


def test_professor_nao_substitui_reserva_de_outro_professor():
    conflitos = [
        {"id_reserva": 5, "papel": PapelUsuario.PROFESSOR}
    ]

    permitido, ids = service._resolver_prioridade(
        PapelUsuario.PROFESSOR, conflitos
    )

    assert permitido is False
    assert ids == []


def test_professor_nao_substitui_reserva_de_admin():
    conflitos = [
        {"id_reserva": 5, "papel": PapelUsuario.ADMIN}
    ]

    permitido, ids = service._resolver_prioridade(
        PapelUsuario.PROFESSOR, conflitos
    )

    assert permitido is False
    assert ids == []


def test_professor_nao_substitui_grupo_com_usuario_nao_aluno():
    conflitos = [
        {"id_reserva": 5, "papel": PapelUsuario.ALUNO},
        {"id_reserva": 6, "papel": PapelUsuario.PROFESSOR},
    ]

    permitido, ids = service._resolver_prioridade(
        PapelUsuario.PROFESSOR, conflitos
    )

    assert permitido is False
    assert ids == []

# CANCELAMENTO DE RESERVAS

@pytest.mark.parametrize(
    "reserva,usuario_ativo,esperado",
    [
        (None, True, False),
        (
            {"id_usuario": 10, "status_reserva": StatusReserva.CANCELADA},
            True,
            False,
        ),
        (
            {"id_usuario": 20, "status_reserva": StatusReserva.CONFIRMADA},
            True,
            False,
        ),
        (
            {"id_usuario": 10, "status_reserva": StatusReserva.CONFIRMADA},
            False,
            False,
        ),
    ],
)
def test_cancelamento_rejeita_situacoes_invalidas(
    monkeypatch, reserva, usuario_ativo, esperado
):
    configurar_usuario_ativo(monkeypatch, usuario_ativo)

    if usuario_ativo:
        conexao = MockConexao(resultado=reserva)
        configurar_conexoes(monkeypatch, conexao)

    resultado = service.cancelar_reserva(5, 10)

    assert resultado is esperado


def test_cancelar_reserva_confirmada(monkeypatch):
    configurar_usuario_ativo(monkeypatch)

    conexao = MockConexao(
        resultado={
            "id_usuario": 10,
            "status_reserva": StatusReserva.CONFIRMADA,
        }
    )
    configurar_conexoes(monkeypatch, conexao)

    resultado = service.cancelar_reserva(5, 10)

    assert resultado is True
    assert conexao.commit_chamado

    sql, valores = conexao.mock_cursor.executado[1]

    assert "UPDATE reservas" in sql
    assert valores == (StatusReserva.CANCELADA,
                       5, 10,
                       StatusReserva.CONFIRMADA,
                       StatusReserva.PENDENTE)

# ALTERAÇÃO DE RESERVAS

def preparar_alteracao(monkeypatch, status=StatusReserva.CONFIRMADA):
    configurar_usuario_ativo(monkeypatch)

    monkeypatch.setattr(
        service,
        "verificar_sala_disponivel",
        lambda id_sala: True,
    )
    monkeypatch.setattr(
        service,
        "obter_conflitos_horario",
        lambda *args, **kwargs: [],
    )
    monkeypatch.setattr(
        service,
        "_papel_do_usuario",
        lambda id_usuario: PapelUsuario.ALUNO,
    )
    monkeypatch.setattr(
        service,
        "_definir_status_reserva",
        lambda id_sala: status,
    )


def test_alterar_reserva_com_sucesso(monkeypatch):
    preparar_alteracao(monkeypatch)

    consulta = MockConexao(
        resultado={
            "id_usuario": 10,
            "status_reserva": StatusReserva.CONFIRMADA,
        }
    )
    atualizacao = MockConexao()

    configurar_conexoes(monkeypatch, consulta, atualizacao)

    resultado = service.alterar_reserva(
        5, 10, 3, DATA, INICIO, FIM
    )

    assert resultado is True
    assert atualizacao.commit_chamado

    sql, valores = atualizacao.mock_cursor.executado[0]

    assert "UPDATE reservas" in sql
    assert valores == (
        3,
        DATA,
        INICIO,
        FIM,
        StatusReserva.CONFIRMADA,
        5,
        10,
        StatusReserva.CONFIRMADA
    )


def test_nao_altera_reserva_de_outro_usuario(monkeypatch):
    preparar_alteracao(monkeypatch)

    consulta = MockConexao(
        resultado={
            "id_usuario": 20,
            "status_reserva": StatusReserva.CONFIRMADA,
        }
    )
    configurar_conexoes(monkeypatch, consulta)

    resultado = service.alterar_reserva(
        5, 10, 3, DATA, INICIO, FIM
    )

    assert resultado is False


def test_nao_altera_reserva_cancelada(monkeypatch):
    preparar_alteracao(monkeypatch)

    consulta = MockConexao(
        resultado={
            "id_usuario": 10,
            "status_reserva": StatusReserva.CANCELADA,
        }
    )
    configurar_conexoes(monkeypatch, consulta)

    resultado = service.alterar_reserva(
        5, 10, 3, DATA, INICIO, FIM
    )

    assert resultado is False


def test_nao_altera_reserva_para_sala_indisponivel(monkeypatch):
    preparar_alteracao(monkeypatch)

    monkeypatch.setattr(
        service,
        "verificar_sala_disponivel",
        lambda id_sala: False,
    )

    consulta = MockConexao(
        resultado={
            "id_usuario": 10,
            "status_reserva": StatusReserva.CONFIRMADA,
        }
    )
    configurar_conexoes(monkeypatch, consulta)

    resultado = service.alterar_reserva(
        5, 10, 3, DATA, INICIO, FIM
    )

    assert resultado is False


def test_alterar_para_laboratorio_volta_para_pendente(monkeypatch):
    preparar_alteracao(monkeypatch, StatusReserva.PENDENTE)

    consulta = MockConexao(
        resultado={
            "id_usuario": 10,
            "status_reserva": StatusReserva.CONFIRMADA,
        }
    )
    atualizacao = MockConexao()

    configurar_conexoes(monkeypatch, consulta, atualizacao)

    resultado = service.alterar_reserva(
        5, 10, 6, DATA, INICIO, FIM
    )

    assert resultado is True

    _, valores = atualizacao.mock_cursor.executado[0]

    assert valores[4] == StatusReserva.PENDENTE

# APROVAÇÃO DE RESERVAS

def preparar_aprovacao(monkeypatch):
    configurar_admin(monkeypatch)

    monkeypatch.setattr(
        service,
        "verificar_sala_disponivel",
        lambda id_sala: True,
    )
    monkeypatch.setattr(
        service,
        "obter_conflitos_horario",
        lambda *args, **kwargs: [],
    )
    monkeypatch.setattr(
        service,
        "_papel_do_usuario",
        lambda id_usuario: PapelUsuario.ALUNO,
    )


def test_usuario_comum_nao_aprova_reserva(monkeypatch):
    configurar_admin(monkeypatch, admin=False)

    resultado = service.aprovar_reserva(5, 10)

    assert resultado is False


def test_admin_aprova_reserva_pendente(monkeypatch):
    preparar_aprovacao(monkeypatch)

    consulta = MockConexao(resultado=RESERVA_PENDENTE)
    atualizacao = MockConexao()

    configurar_conexoes(monkeypatch, consulta, atualizacao)

    resultado = service.aprovar_reserva(5, 99)

    assert resultado is True
    assert atualizacao.commit_chamado

    sql, valores = atualizacao.mock_cursor.executado[0]

    assert "UPDATE reservas" in sql
    assert valores == (StatusReserva.CONFIRMADA, 5,
                       StatusReserva.PENDENTE)


@pytest.mark.parametrize(
    "status",
    [
        StatusReserva.CONFIRMADA,
        StatusReserva.CANCELADA,
    ],
)
def test_admin_nao_aprova_reserva_que_nao_esta_pendente(
    monkeypatch, status
):
    preparar_aprovacao(monkeypatch)

    consulta = MockConexao(
        resultado={
            **RESERVA_PENDENTE,
            "status_reserva": status,
        }
    )
    configurar_conexoes(monkeypatch, consulta)

    resultado = service.aprovar_reserva(5, 99)

    assert resultado is False


def test_admin_nao_aprova_reserva_inexistente(monkeypatch):
    preparar_aprovacao(monkeypatch)

    consulta = MockConexao(resultado=None)
    configurar_conexoes(monkeypatch, consulta)

    assert service.aprovar_reserva(999, 99) is False


def test_admin_nao_aprova_reserva_de_sala_indisponivel(monkeypatch):
    preparar_aprovacao(monkeypatch)

    monkeypatch.setattr(
        service,
        "verificar_sala_disponivel",
        lambda id_sala: False,
    )

    consulta = MockConexao(resultado=RESERVA_PENDENTE)
    configurar_conexoes(monkeypatch, consulta)

    assert service.aprovar_reserva(5, 99) is False


def test_admin_nao_aprova_reserva_com_conflito_nao_permitido(monkeypatch):
    preparar_aprovacao(monkeypatch)

    monkeypatch.setattr(
        service,
        "obter_conflitos_horario",
        lambda *args, **kwargs: [
            {"id_reserva": 7, "papel": PapelUsuario.PROFESSOR}
        ],
    )

    consulta = MockConexao(resultado=RESERVA_PENDENTE)
    configurar_conexoes(monkeypatch, consulta)

    assert service.aprovar_reserva(5, 99) is False

# NEGAÇÃO DE RESERVAS

def test_usuario_comum_nao_nega_reserva(monkeypatch):
    configurar_admin(monkeypatch, admin=False)

    resultado = service.negar_reserva(5, 10)

    assert resultado is False


def test_admin_nega_reserva_pendente(monkeypatch):
    configurar_admin(monkeypatch)

    conexao = MockConexao(
        resultado=RESERVA_PENDENTE
    )
    configurar_conexoes(monkeypatch, conexao)

    resultado = service.negar_reserva(5, 99)

    assert resultado is True
    assert conexao.commit_chamado

    sql, valores = conexao.mock_cursor.executado[1]

    assert "UPDATE reservas" in sql
    assert valores == (StatusReserva.CANCELADA, 5,
                       StatusReserva.PENDENTE)


def test_admin_nao_nega_reserva_inexistente(monkeypatch):
    configurar_admin(monkeypatch)

    conexao = MockConexao(resultado=None)
    configurar_conexoes(monkeypatch, conexao)

    assert service.negar_reserva(999, 99) is False


@pytest.mark.parametrize(
    "status",
    [
        StatusReserva.CONFIRMADA,
        StatusReserva.CANCELADA,
    ],
)
def test_admin_nao_nega_reserva_que_nao_esta_pendente(
    monkeypatch, status
):
    configurar_admin(monkeypatch)

    conexao = MockConexao(
        resultado={"status_reserva": status}
    )
    configurar_conexoes(monkeypatch, conexao)

    assert service.negar_reserva(5, 99) is False

# CONSULTAS DE RESERVAS

def test_consultar_proxima_reserva_retorna_resultado(monkeypatch):
    resultado_banco = {
        "id_reserva": 5,
        "hora_inicio": timedelta(hours=19),
        "hora_fim": timedelta(hours=21),
    }

    conexao = MockConexao(resultado=resultado_banco)
    configurar_conexoes(monkeypatch, conexao)

    resultado = service.consultar_proxima_reserva(10, DATA)

    assert resultado["id_reserva"] == 5
    assert resultado["hora_inicio"] == time(19, 0)
    assert resultado["hora_fim"] == time(21, 0)


def test_consultar_proxima_reserva_sem_resultado(monkeypatch):
    conexao = MockConexao(resultado=None)
    configurar_conexoes(monkeypatch, conexao)

    assert service.consultar_proxima_reserva(10, DATA) is None


def test_consultar_reservas_pendentes_exige_admin(monkeypatch):
    exigir_admin = Mock()
    monkeypatch.setattr(
        service.usuarios_service,
        "exigir_admin",
        exigir_admin,
    )

    conexao = MockConexao(
        resultados=[
            {
                "id_reserva": 5,
                "hora_inicio": timedelta(hours=19),
                "hora_fim": timedelta(hours=21),
            }
        ]
    )
    configurar_conexoes(monkeypatch, conexao)

    resultado = service.consultar_reservas_pendentes(99)

    exigir_admin.assert_called_once_with(99)
    assert len(resultado) == 1
    assert resultado[0]["hora_inicio"] == time(19, 0)


def test_consultar_reservas_usuario_adiciona_pode_alterar(monkeypatch):
    conexao = MockConexao(
        resultados=[
            {
                "id_reserva": 5,
                "status_reserva": StatusReserva.CONFIRMADA,
                "hora_inicio": timedelta(hours=19),
                "hora_fim": timedelta(hours=21),
            },
            {
                "id_reserva": 6,
                "status_reserva": StatusReserva.CANCELADA,
                "hora_inicio": timedelta(hours=14),
                "hora_fim": timedelta(hours=15),
            },
        ]
    )
    configurar_conexoes(monkeypatch, conexao)

    resultado = service.consultar_reservas_usuario(10)

    assert resultado[0]["pode_alterar"] is True
    assert resultado[1]["pode_alterar"] is False

    assert resultado[0]["hora_inicio"] == time(19, 0)
    assert resultado[1]["hora_fim"] == time(15, 0)


def test_pode_gerenciar_pendencias_verifica_admin(monkeypatch):
    monkeypatch.setattr(
        service.usuarios_service,
        "checar_admin",
        lambda id_usuario: id_usuario == 99,
    )

    assert service.pode_gerenciar_pendencias(99) is True
    assert service.pode_gerenciar_pendencias(10) is False

# FUNÇÕES AUXILIARES

def test_definir_status_para_laboratorio(monkeypatch):
    monkeypatch.setattr(
        service,
        "descobre_tipo_sala",
        lambda id_sala: TipoSala.LABORATORIO,
    )

    assert service._definir_status_reserva(6) == StatusReserva.PENDENTE


def test_definir_status_para_auditorio(monkeypatch):
    monkeypatch.setattr(
        service,
        "descobre_tipo_sala",
        lambda id_sala: TipoSala.AUDITORIO,
    )

    assert service._definir_status_reserva(11) == StatusReserva.PENDENTE


def test_definir_status_para_sala_comum(monkeypatch):
    monkeypatch.setattr(
        service,
        "descobre_tipo_sala",
        lambda id_sala: TipoSala.SALA,
    )

    assert service._definir_status_reserva(2) == StatusReserva.CONFIRMADA


def test_definir_status_para_tipo_desconhecido(monkeypatch):
    monkeypatch.setattr(
        service,
        "descobre_tipo_sala",
        lambda id_sala: None,
    )

    assert service._definir_status_reserva(999) is None


def test_descobre_tipo_sala_retorna_tipo(monkeypatch):
    conexao = MockConexao(
        resultado={"tipo_sala": TipoSala.LABORATORIO}
    )
    configurar_conexoes(monkeypatch, conexao)

    assert service.descobre_tipo_sala(6) == TipoSala.LABORATORIO


def test_descobre_tipo_sala_inexistente(monkeypatch):
    conexao = MockConexao(resultado=None)
    configurar_conexoes(monkeypatch, conexao)

    assert service.descobre_tipo_sala(999) is None


def test_cancelar_reservas_substituidas_sem_ids_nao_executa_sql():
    cursor = MockCursor()

    service._cancelar_reservas_substituidas(cursor, [])

    assert cursor.executado == []


def test_cancelar_reservas_substituidas_executa_update():
    cursor = MockCursor()

    service._cancelar_reservas_substituidas(cursor, [5, 6])

    assert len(cursor.executado) == 1

    sql, valores = cursor.executado[0]

    assert "UPDATE reservas" in sql
    assert "IN (%s, %s)" in sql
    assert valores == (
        StatusReserva.CANCELADA,
        5,
        6,
        StatusReserva.CONFIRMADA,
        StatusReserva.PENDENTE,
    )


def test_normalizar_horarios_converte_timedelta():
    reserva = {
        "hora_inicio": timedelta(hours=8, minutes=30),
        "hora_fim": timedelta(hours=10),
    }

    service.normalizar_horarios(reserva)

    assert reserva["hora_inicio"] == time(8, 30)
    assert reserva["hora_fim"] == time(10, 0)


def test_normalizar_horarios_preserva_valores_time():
    reserva = {
        "hora_inicio": time(8, 30),
        "hora_fim": time(10, 0),
    }

    service.normalizar_horarios(reserva)

    assert reserva["hora_inicio"] == time(8, 30)
    assert reserva["hora_fim"] == time(10, 0)
