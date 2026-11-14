import time
import streamlit as st

_CHAVE_USUARIO = "usuario_logado"
_CHAVE_EXPIRA = "sessao_expira_em"
TEMPO_INATIVIDADE_SEGUNDOS = 1800   # 30 minutos


def login_sessao(usuario):
    st.session_state[_CHAVE_USUARIO] = usuario
    st.session_state[_CHAVE_EXPIRA] = time.time() + TEMPO_INATIVIDADE_SEGUNDOS


def logout_sessao():
    for chave in (_CHAVE_USUARIO, _CHAVE_EXPIRA):
        if chave in st.session_state:
            del st.session_state[chave]


def usuario_logado():
    usuario = st.session_state.get(_CHAVE_USUARIO)
    if usuario is None:
        return None

    expira_em = st.session_state.get(_CHAVE_EXPIRA, 0)
    if time.time() > expira_em:
        logout_sessao()
        return None

    # renova a janela de inatividade a cada interação
    st.session_state[_CHAVE_EXPIRA] = time.time() + TEMPO_INATIVIDADE_SEGUNDOS
    return usuario


def esta_logado() -> bool:
    return usuario_logado() is not None
