import streamlit as st

_CHAVE_USUARIO = "usuario_logado"

def login_sessao(usuario):
    st.session_state[_CHAVE_USUARIO] = usuario

def logout_sessao():
    if _CHAVE_USUARIO in st.session_state:
        del st.session_state[_CHAVE_USUARIO]

def usuario_logado():
    return st.session_state.get(_CHAVE_USUARIO)

def esta_logado() -> bool:
    return usuario_logado() is not None