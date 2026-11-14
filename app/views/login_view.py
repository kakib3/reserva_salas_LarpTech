import time
import streamlit as st
from app.controllers import usuarios_controller
from app.utils.sessao import login_sessao

MAX_TENTATIVAS = 5
BLOQUEIO_SEGUNDOS = 300   # 5 minutos


def render():
    st.title("Login")

    agora = time.time()
    bloqueado_ate = st.session_state.get("login_bloqueado_ate", 0)

    if bloqueado_ate and agora >= bloqueado_ate:
        # O bloqueio acabou: recomeça a contagem, senão o primeiro erro bloquearia de novo.
        st.session_state["login_tentativas"] = 0
        st.session_state["login_bloqueado_ate"] = 0
        bloqueado_ate = 0

    if agora < bloqueado_ate:
        restante = int(bloqueado_ate - agora)
        st.error(f"Muitas tentativas. Tente novamente em {restante} segundos.")
        return

    tentativas = st.session_state.get("login_tentativas", 0)

    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        sucesso, mensagem, usuario = (
            usuarios_controller.fazer_login(email, senha)
        )

        if sucesso:
            st.session_state["login_tentativas"] = 0
            st.session_state["login_bloqueado_ate"] = 0
            login_sessao(usuario)
            st.success(mensagem)
            st.rerun()

        else:
            tentativas += 1
            st.session_state["login_tentativas"] = tentativas

            if tentativas >= MAX_TENTATIVAS:
                st.session_state["login_bloqueado_ate"] = agora + BLOQUEIO_SEGUNDOS
                st.error("Muitas tentativas. Acesso bloqueado temporariamente.")
            else:
                st.error(mensagem)
