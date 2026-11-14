import pytest

from app.views import login_view


class _StreamlitFalso:
    """Simula só o que a tela de login usa."""

    def __init__(self):
        self.session_state = {}
        self.clicou = False
        self.erros = []
        self.sucessos = []
        self.rerun_chamado = False

    def title(self, _):
        pass

    def text_input(self, rotulo, type=None):
        return "ana@teste.com"

    def button(self, _):
        return self.clicou

    def error(self, mensagem):
        self.erros.append(mensagem)

    def success(self, mensagem):
        self.sucessos.append(mensagem)

    def rerun(self):
        self.rerun_chamado = True


@pytest.fixture
def ambiente(monkeypatch):
    st = _StreamlitFalso()
    agora = {"t": 1000.0}
    resultado = {"login": (False, "Email ou senha inválidos.", None)}

    monkeypatch.setattr(login_view, "st", st)
    monkeypatch.setattr(login_view.time, "time", lambda: agora["t"])
    monkeypatch.setattr(
        login_view.usuarios_controller, "fazer_login",
        lambda email, senha: resultado["login"]
    )
    monkeypatch.setattr(login_view, "login_sessao", lambda usuario: st.session_state.update(usuario=usuario))

    return st, agora, resultado


def _tentar_login(st):
    st.clicou = True
    st.erros.clear()
    login_view.render()


def test_erros_ate_o_limite_mostram_a_mensagem_normal(ambiente):
    st, _, _ = ambiente

    for _ in range(login_view.MAX_TENTATIVAS - 1):
        _tentar_login(st)

    assert st.erros == ["Email ou senha inválidos."]
    assert st.session_state.get("login_bloqueado_ate", 0) == 0


def test_na_quinta_falha_o_acesso_e_bloqueado(ambiente):
    st, agora, _ = ambiente

    for _ in range(login_view.MAX_TENTATIVAS):
        _tentar_login(st)

    assert "bloqueado temporariamente" in st.erros[0]
    assert st.session_state["login_bloqueado_ate"] == agora["t"] + login_view.BLOQUEIO_SEGUNDOS


def test_durante_o_bloqueio_nao_tenta_o_login_e_mostra_o_tempo_restante(ambiente):
    st, agora, resultado = ambiente
    for _ in range(login_view.MAX_TENTATIVAS):
        _tentar_login(st)

    chamadas = []
    resultado["login"] = (True, "ok", "ana")
    login_view.usuarios_controller.fazer_login = lambda *a: chamadas.append(a) or resultado["login"]
    agora["t"] += 100

    _tentar_login(st)

    assert chamadas == []
    assert "200 segundos" in st.erros[0]


def test_depois_do_bloqueio_o_contador_recomeca_do_zero(ambiente):
    st, agora, _ = ambiente
    for _ in range(login_view.MAX_TENTATIVAS):
        _tentar_login(st)

    agora["t"] += login_view.BLOQUEIO_SEGUNDOS + 1
    _tentar_login(st)

    # Um erro depois do bloqueio é o primeiro erro, e não bloqueia de novo.
    assert st.erros == ["Email ou senha inválidos."]
    assert st.session_state["login_tentativas"] == 1


def test_login_correto_zera_as_tentativas(ambiente):
    st, _, resultado = ambiente
    _tentar_login(st)
    _tentar_login(st)

    resultado["login"] = (True, "Bem-vindo!", "ana")
    _tentar_login(st)

    assert st.session_state["login_tentativas"] == 0
    assert st.session_state["usuario"] == "ana"
    assert st.rerun_chamado is True
