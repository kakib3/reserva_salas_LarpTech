"""Fixtures dos testes de integração com MySQL.

Ideia central: os services rodam de verdade, com o conexao.py de verdade,
mas apontando para um banco SEPARADO (`*_test`). Nada é mockado no caminho
do banco. Só o e-mail é trocado por um gravador, para não enviar mensagens.

Sem as variáveis de ambiente abaixo, todos os testes desta pasta são pulados
(é isso que acontece no GitHub Actions hoje, sem quebrar o CI).

    LARPTECH_TEST_DB_HOST      LARPTECH_TEST_DB_NAME   (precisa terminar em _test)
    LARPTECH_TEST_DB_USER      LARPTECH_TEST_DB_PASSWORD
    LARPTECH_TEST_DB_PORT      (opcional, padrão 3306)
    LARPTECH_TEST_DB_SSL_CA    (opcional, caminho do ca.pem; o Aiven exige)
"""
import datetime as dt
import functools
import os
import pathlib

import mysql.connector
import pytest
import streamlit as st

from app.messaging import notificacoes_service
from app.models import conexao
from app.utils import relogio, salas_ocultas, seguranca

PASTA = pathlib.Path(__file__).parent
SENHA_PADRAO = "Senha123"
TABELAS = ("reservas", "salas", "usuarios")  # ordem segura para limpar


@pytest.fixture(autouse=True)
def _bloquear_banco_real():
    """Sobrescreve a trava de tests/conftest.py: aqui o banco (de teste) é usado de verdade."""


# ----------------------------------------------------------------------------
# Marcação automática: tudo desta pasta recebe @pytest.mark.integration
# (permite `pytest -m "not integration"` e `pytest -m integration`)
# ----------------------------------------------------------------------------
def pytest_collection_modifyitems(items):
    for item in items:
        caminho = pathlib.Path(str(getattr(item, "path", None) or item.fspath))
        if PASTA in caminho.parents:
            item.add_marker(pytest.mark.integration)


# ----------------------------------------------------------------------------
# Configuração e segurança
# ----------------------------------------------------------------------------
@pytest.fixture(scope="session")
def config_banco():
    obrigatorias = (
        "LARPTECH_TEST_DB_HOST",
        "LARPTECH_TEST_DB_NAME",
        "LARPTECH_TEST_DB_USER",
        "LARPTECH_TEST_DB_PASSWORD",
    )
    faltando = [v for v in obrigatorias if not os.environ.get(v)]
    if faltando:
        pytest.skip("Testes de integração pulados. Defina: " + ", ".join(faltando))

    nome = os.environ["LARPTECH_TEST_DB_NAME"]
    if not nome.lower().endswith("_test"):
        # Os testes apagam e recriam as tabelas: NUNCA rodar em banco real.
        pytest.exit(
            f"Recusado: o banco '{nome}' não termina em '_test'. "
            "Os testes de integração apagam todas as tabelas.",
            returncode=2,
        )

    return {
        "host": os.environ["LARPTECH_TEST_DB_HOST"],
        "port": int(os.environ.get("LARPTECH_TEST_DB_PORT", "3306")),
        "database": nome,
        "user": os.environ["LARPTECH_TEST_DB_USER"],
        "password": os.environ["LARPTECH_TEST_DB_PASSWORD"],
        "ssl_ca": os.environ.get("LARPTECH_TEST_DB_SSL_CA") or None,
    }


def _conectar_admin(config):
    kwargs = dict(
        host=config["host"],
        port=config["port"],
        database=config["database"],
        user=config["user"],
        password=config["password"],
        autocommit=True,  # sem isso, esta conexão não enxerga o que os services commitam
    )
    if config["ssl_ca"]:
        kwargs["ssl_ca"] = config["ssl_ca"]
    return mysql.connector.connect(**kwargs)


def _comandos_sql(arquivo):
    linhas = [
        linha for linha in arquivo.read_text(encoding="utf-8").splitlines()
        if not linha.strip().startswith("--")
    ]
    return [c.strip() for c in "\n".join(linhas).split(";") if c.strip()]


@pytest.fixture(scope="session")
def _conexao_admin(config_banco):
    conn = _conectar_admin(config_banco)
    yield conn
    conn.close()


@pytest.fixture(scope="session", autouse=True)
def _banco_preparado(config_banco, _conexao_admin):
    """Aponta o app para o banco de teste e recria o schema uma vez por sessão."""
    segredos = {"mysql": dict(config_banco)}

    with pytest.MonkeyPatch.context() as mp:
        # Substitui TODO o st.secrets: mesmo que exista um secrets.toml de
        # produção na máquina, ele não é lido (e [email] some também).
        mp.setattr(st, "secrets", segredos)
        conexao.obter_pool.clear()  # descarta pool criado com outras credenciais

        cursor = _conexao_admin.cursor()
        for comando in _comandos_sql(PASTA / "schema.sql"):
            cursor.execute(comando)
        cursor.close()

        yield

        conexao.obter_pool.clear()


# ----------------------------------------------------------------------------
# Acesso direto ao banco (independente do código que está sendo testado)
# ----------------------------------------------------------------------------
class Banco:
    def __init__(self, conn):
        self._conn = conn

    def _cursor(self):
        if not self._conn.is_connected():
            self._conn.reconnect(attempts=3, delay=1)
        return self._conn.cursor(dictionary=True)

    @staticmethod
    def _normalizar(linha):
        # TIME volta como timedelta; converte para datetime.time
        for chave, valor in linha.items():
            if isinstance(valor, dt.timedelta):
                s = int(valor.total_seconds())
                linha[chave] = dt.time(s // 3600, (s % 3600) // 60, s % 60)
        return linha

    def executar(self, sql, params=()):
        cursor = self._cursor()
        try:
            cursor.execute(sql, params)
            return cursor.lastrowid
        finally:
            cursor.close()

    def todos(self, sql, params=()):
        cursor = self._cursor()
        try:
            cursor.execute(sql, params)
            return [self._normalizar(l) for l in cursor.fetchall()]
        finally:
            cursor.close()

    def um(self, sql, params=()):
        linhas = self.todos(sql, params)
        return linhas[0] if linhas else None

    def contar(self, tabela, onde="1 = 1", params=()):
        return self.um(f"SELECT COUNT(*) AS n FROM {tabela} WHERE {onde}", params)["n"]


@pytest.fixture
def banco(_conexao_admin):
    return Banco(_conexao_admin)


@pytest.fixture(autouse=True)
def _estado_limpo(banco):
    """Cada teste começa com tabelas vazias (IDs recomeçam em 1) e sem salas ocultas."""
    banco.executar("SET FOREIGN_KEY_CHECKS = 0")
    for tabela in TABELAS:
        banco.executar(f"TRUNCATE TABLE {tabela}")
    banco.executar("SET FOREIGN_KEY_CHECKS = 1")

    for id_sala in list(salas_ocultas.listar_ocultas()):
        salas_ocultas.mostrar_sala(id_sala)


@pytest.fixture(autouse=True)
def emails(monkeypatch):
    """Grava os e-mails em vez de enviar. Retorna a lista de envios."""
    enviados = []

    def enviar_falso(destinatario, assunto, corpo):
        enviados.append({"destinatario": destinatario, "assunto": assunto, "corpo": corpo})
        return True

    monkeypatch.setattr(notificacoes_service, "enviar_email", enviar_falso)
    return enviados


# ----------------------------------------------------------------------------
# Fábricas de dados (inserem direto no banco, sem passar pelos services)
# ----------------------------------------------------------------------------
@functools.cache
def _hash_padrao():
    # bcrypt é lento de propósito: calcula uma vez só.
    return seguranca.gerar_hash_senha(SENHA_PADRAO)


@pytest.fixture
def criar_usuario_db(banco):
    contador = {"n": 0}

    def fazer(papel="Aluno", nome=None, email=None, status="Ativo", telefone="69999990000"):
        contador["n"] += 1
        n = contador["n"]
        return banco.executar(
            """INSERT INTO usuarios (nome, email, telefone, papel, senha, status_usuario)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (nome or f"Usuario {n}", email or f"usuario{n}@teste.com", telefone,
             papel, _hash_padrao(), status),
        )

    return fazer


@pytest.fixture
def criar_sala_db(banco):
    contador = {"n": 0}

    def fazer(tipo="Sala", status="Disponivel", capacidade=30, nome=None):
        contador["n"] += 1
        return banco.executar(
            """INSERT INTO salas (nome, capacidade, predio, andar, status_sala, tipo_sala)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (nome or f"Sala{contador['n']:02d}", capacidade, "BlocoA", "1", status, tipo),
        )

    return fazer


@pytest.fixture
def criar_reserva_db(banco):
    def fazer(id_usuario, id_sala, data, inicio, fim, status="Confirmada"):
        return banco.executar(
            """INSERT INTO reservas (id_usuario, id_sala, data_reserva, hora_inicio,
                                     hora_fim, status_reserva, criado_em)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (id_usuario, id_sala, data, inicio, fim, status, relogio.hoje()),
        )

    return fazer


@pytest.fixture
def id_admin(criar_usuario_db):
    return criar_usuario_db("Admin", nome="Admin Teste", email="admin@teste.com")


@pytest.fixture
def id_professor(criar_usuario_db):
    return criar_usuario_db("Professor", nome="Professor Teste", email="prof@teste.com")


@pytest.fixture
def id_aluno(criar_usuario_db):
    return criar_usuario_db("Aluno", nome="Aluno Teste", email="aluno@teste.com")


@pytest.fixture
def id_sala(criar_sala_db):
    return criar_sala_db("Sala")


@pytest.fixture
def id_lab(criar_sala_db):
    return criar_sala_db("Laboratorio", nome="Lab01")


# ----------------------------------------------------------------------------
# Datas: sempre no futuro, em relação ao relógio do app (fuso de Porto Velho),
# para não depender do horário em que o teste roda.
# ----------------------------------------------------------------------------
def _proximo_dia_da_semana(dia):
    data = relogio.hoje() + dt.timedelta(days=7)
    while data.weekday() != dia:
        data += dt.timedelta(days=1)
    return data


@pytest.fixture
def segunda():
    return _proximo_dia_da_semana(0)


@pytest.fixture
def domingo():
    return _proximo_dia_da_semana(6)
