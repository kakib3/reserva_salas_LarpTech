"""Mensagens que sobrevivem ao st.rerun()."""
import pytest

from app.utils import mensagens


class StreamlitFalso:
    def __init__(self):
        self.session_state = {}
        self.exibidas = []

    def __getattr__(self, tipo):
        if tipo in ("success", "error", "warning", "info"):
            return lambda texto: self.exibidas.append((tipo, texto))
        raise AttributeError(tipo)


@pytest.fixture
def st(monkeypatch):
    falso = StreamlitFalso()
    monkeypatch.setattr(mensagens, "st", falso)
    return falso


def test_mensagem_agendada_aparece_na_proxima_exibicao(st):
    mensagens.agendar("sucesso", "Reserva cancelada.")

    assert st.exibidas == []             # ainda não foi exibida
    mensagens.exibir()

    assert st.exibidas == [("success", "Reserva cancelada.")]


def test_mensagem_aparece_uma_unica_vez(st):
    mensagens.agendar("sucesso", "Feito.")

    mensagens.exibir()
    mensagens.exibir()

    assert st.exibidas == [("success", "Feito.")]


def test_varias_mensagens_mantem_a_ordem_e_o_tipo(st):
    mensagens.agendar("sucesso", "um")
    mensagens.agendar("erro", "dois")
    mensagens.agendar("aviso", "três")
    mensagens.agendar("info", "quatro")

    mensagens.exibir()

    assert st.exibidas == [("success", "um"), ("error", "dois"), ("warning", "três"), ("info", "quatro")]


def test_agendar_resultado_escolhe_sucesso_ou_erro(st):
    mensagens.agendar_resultado(True, "ok")
    mensagens.agendar_resultado(False, "falhou")

    mensagens.exibir()

    assert st.exibidas == [("success", "ok"), ("error", "falhou")]


def test_tipo_desconhecido_cai_em_info(st):
    mensagens.agendar("qualquer", "texto")

    mensagens.exibir()

    assert st.exibidas == [("info", "texto")]


def test_exibir_sem_nada_agendado_nao_faz_nada(st):
    mensagens.exibir()

    assert st.exibidas == []
