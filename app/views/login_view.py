import streamlit as st
from app.controllers import usuarios_controller
from app.utils.sessao import login_sessao


def render():
    st.title("Login")

    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        sucesso, mensagem, usuario = usuarios_controller.fazer_login(email, senha)
        if sucesso:
            login_sessao(usuario)
            st.success(mensagem)
            st.rerun()
        else:
            st.error(mensagem)