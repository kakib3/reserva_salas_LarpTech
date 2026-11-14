
import pytest

from app.models import dados


# MOCKS DO BANCO DE DADOS

class MockCursor:
    def __init__(self, resultado=None, erro_execute=None, erro_fetchall=None):
        self.resultado = resultado if resultado is not None else []
        self.erro_execute = erro_execute
        self.erro_fetchall = erro_fetchall

        self.sql_executado = None
        self.valores = None
        self.fechado = False

    def execute(self, sql, valores=None):
        self.sql_executado = sql
        self.valores = valores

        if self.erro_execute:
            raise self.erro_execute

    def fetchall(self):
        if self.erro_fetchall:
            raise self.erro_fetchall

        return self.resultado

    def close(self):
        self.fechado = True


class MockConexao:
    def __init__(self, resultado=None, erro_execute=None, erro_fetchall=None):
        self.mock_cursor = MockCursor(
            resultado,
            erro_execute,
            erro_fetchall,
        )

        self.fechado = False
        self.dictionary_utilizado = False

    def cursor(self, dictionary=False, **kwargs):
        self.dictionary_utilizado = dictionary
        return self.mock_cursor

    def close(self):
        self.fechado = True


def configurar_conexao(monkeypatch, conexao):
    monkeypatch.setattr(
        dados,
        "conectar_banco",
        lambda: conexao,
    )


def verificar_fechamento(conexao):
    assert conexao.mock_cursor.fechado is True
    assert conexao.fechado is True

# CARREGAR USUÁRIOS

def test_carregar_usuarios_retorna_lista_de_usuarios(monkeypatch):
    usuarios = [
        {
            "id_usuario": 1,
            "nome": "Joao",
            "email": "joao@email.com",
            "telefone": "69999999999",
            "papel": "Aluno",
            "status_usuario": "Ativo",
        },
        {
            "id_usuario": 2,
            "nome": "Maria",
            "email": "maria@email.com",
            "telefone": "69888888888",
            "papel": "Admin",
            "status_usuario": "Ativo",
        },
    ]

    conexao = MockConexao(resultado=usuarios)
    configurar_conexao(monkeypatch, conexao)

    resultado = dados.carregar_usuarios()

    assert resultado == usuarios
    assert conexao.dictionary_utilizado is True

    sql = conexao.mock_cursor.sql_executado

    assert "FROM usuarios" in sql
    assert "id_usuario" in sql
    assert "nome" in sql
    assert "email" in sql
    assert "telefone" in sql
    assert "papel" in sql
    assert "status_usuario" in sql

    verificar_fechamento(conexao)


def test_carregar_usuarios_sem_registros(monkeypatch):
    conexao = MockConexao(resultado=[])
    configurar_conexao(monkeypatch, conexao)

    resultado = dados.carregar_usuarios()

    assert resultado == []

    verificar_fechamento(conexao)

# CARREGAR SALAS

def test_carregar_salas_retorna_lista_de_salas(monkeypatch):
    salas = [
        {
            "id_sala": 1,
            "nome": "Sala 01",
            "capacidade": 30,
            "status_sala": "Disponivel",
        },
        {
            "id_sala": 2,
            "nome": "Laboratorio 01",
            "capacidade": 25,
            "status_sala": "Disponivel",
        },
    ]

    conexao = MockConexao(resultado=salas)
    configurar_conexao(monkeypatch, conexao)

    resultado = dados.carregar_salas()

    assert resultado == salas
    assert conexao.dictionary_utilizado is True
    assert "SELECT * FROM salas" in conexao.mock_cursor.sql_executado

    verificar_fechamento(conexao)


def test_carregar_salas_sem_registros(monkeypatch):
    conexao = MockConexao(resultado=[])
    configurar_conexao(monkeypatch, conexao)

    resultado = dados.carregar_salas()

    assert resultado == []

    verificar_fechamento(conexao)

# CARREGAR RESERVAS

def test_carregar_reservas_retorna_lista_de_reservas(monkeypatch):
    reservas = [
        {
            "id_reserva": 1,
            "id_usuario": 10,
            "id_sala": 2,
            "status_reserva": "Confirmada",
        },
        {
            "id_reserva": 2,
            "id_usuario": 11,
            "id_sala": 6,
            "status_reserva": "Pendente",
        },
    ]

    conexao = MockConexao(resultado=reservas)
    configurar_conexao(monkeypatch, conexao)

    resultado = dados.carregar_reservas()

    assert resultado == reservas
    assert conexao.dictionary_utilizado is True
    assert "SELECT * FROM reservas" in conexao.mock_cursor.sql_executado

    verificar_fechamento(conexao)


def test_carregar_reservas_sem_registros(monkeypatch):
    conexao = MockConexao(resultado=[])
    configurar_conexao(monkeypatch, conexao)

    resultado = dados.carregar_reservas()

    assert resultado == []

    verificar_fechamento(conexao)

# OBTER RESERVAS DE UMA SALA

def test_obter_reservas_da_sala_sem_data(monkeypatch):
    reservas = [
        {
            "id_reserva": 1,
            "id_sala": 3,
            "status_reserva": "Confirmada",
        },
        {
            "id_reserva": 2,
            "id_sala": 3,
            "status_reserva": "Pendente",
        },
    ]

    conexao = MockConexao(resultado=reservas)
    configurar_conexao(monkeypatch, conexao)

    resultado = dados.obter_reservas_da_sala(3)

    assert resultado == reservas

    sql = conexao.mock_cursor.sql_executado

    assert "WHERE id_sala = %s" in sql
    assert "data_reserva" not in sql
    assert conexao.mock_cursor.valores == (3,)

    verificar_fechamento(conexao)


def test_obter_reservas_da_sala_com_data(monkeypatch):
    data_reserva = "2026-11-16"

    reservas = [
        {
            "id_reserva": 1,
            "id_sala": 3,
            "data_reserva": data_reserva,
        }
    ]

    conexao = MockConexao(resultado=reservas)
    configurar_conexao(monkeypatch, conexao)

    resultado = dados.obter_reservas_da_sala(
        3,
        data_reserva,
    )

    assert resultado == reservas

    sql = conexao.mock_cursor.sql_executado

    assert "id_sala = %s" in sql
    assert "data_reserva = %s" in sql
    assert conexao.mock_cursor.valores == (3, data_reserva)

    verificar_fechamento(conexao)


def test_obter_reservas_da_sala_sem_resultados(monkeypatch):
    conexao = MockConexao(resultado=[])
    configurar_conexao(monkeypatch, conexao)

    resultado = dados.obter_reservas_da_sala(999)

    assert resultado == []

    verificar_fechamento(conexao)

# TRATAMENTO DE ERROS E LIBERAÇÃO DE RECURSOS

def test_erro_durante_execucao_da_consulta_fecha_conexao(monkeypatch):
    conexao = MockConexao(
        erro_execute=RuntimeError("Erro simulado na consulta"),
    )
    configurar_conexao(monkeypatch, conexao)

    with pytest.raises(RuntimeError, match="Erro simulado"):
        dados.carregar_usuarios()

    verificar_fechamento(conexao)


def test_erro_durante_fetchall_fecha_conexao(monkeypatch):
    conexao = MockConexao(
        erro_fetchall=RuntimeError("Erro simulado ao buscar registros"),
    )
    configurar_conexao(monkeypatch, conexao)

    with pytest.raises(RuntimeError, match="Erro simulado"):
        dados.carregar_salas()

    verificar_fechamento(conexao)
