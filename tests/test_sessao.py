import pytest

from app.utils import sessao


class _StreamlitFalso:
    def __init__(self):
        self.session_state = {}


@pytest.fixture
def relogio(monkeypatch):
    """Troca o streamlit por um dicionário e controla o tempo."""
    monkeypatch.setattr(sessao, "st", _StreamlitFalso())
    agora = {"t": 1000.0}
    monkeypatch.setattr(sessao.time, "time", lambda: agora["t"])
    return agora


def test_sem_login_nao_ha_usuario(relogio):
    assert sessao.usuario_logado() is None
    assert sessao.esta_logado() is False


def test_login_deixa_o_usuario_logado(relogio):
    sessao.login_sessao("ana")

    assert sessao.usuario_logado() == "ana"
    assert sessao.esta_logado() is True


def test_sessao_expira_apos_o_tempo_de_inatividade(relogio):
    sessao.login_sessao("ana")

    relogio["t"] += sessao.TEMPO_INATIVIDADE_SEGUNDOS + 1

    assert sessao.usuario_logado() is None
    assert "usuario_logado" not in sessao.st.session_state
    assert "sessao_expira_em" not in sessao.st.session_state


def test_atividade_renova_a_janela_de_inatividade(relogio):
    sessao.login_sessao("ana")

    # Interage duas vezes, cada uma antes de expirar. Somando, passa do limite inicial.
    relogio["t"] += sessao.TEMPO_INATIVIDADE_SEGUNDOS - 60
    assert sessao.usuario_logado() == "ana"

    relogio["t"] += sessao.TEMPO_INATIVIDADE_SEGUNDOS - 60
    assert sessao.usuario_logado() == "ana"


def test_logout_limpa_usuario_e_expiracao(relogio):
    sessao.login_sessao("ana")

    sessao.logout_sessao()

    assert sessao.usuario_logado() is None
    assert sessao.st.session_state == {}


def test_logout_sem_login_nao_da_erro(relogio):
    sessao.logout_sessao()

    assert sessao.st.session_state == {}
