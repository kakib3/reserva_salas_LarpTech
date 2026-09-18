import streamlit as st

from app.views.login_view import render as render_login
from app.views.home_view import render as render_home
from app.views.salas_view import render as render_salas
from app.views.detalhes_sala_view import render as render_detalhes_sala
from app.views.reservar_view import render as render_reservar
from app.views.minhas_reservas_view import render as render_minhas_reservas
from app.utils.sessao import usuario_logado, logout_sessao


def home_page():
    render_home()


def salas_page():
    render_salas()


def detalhes_sala_page():
    render_detalhes_sala()


def reservar_page():
    render_reservar()


def minhas_reservas_page():
    render_minhas_reservas()


usuario = usuario_logado()

if usuario is None:
    pagina_login = st.Page(render_login, title="Login")
    navigation = st.navigation([pagina_login])
    navigation.run()
else:
    pagina_inicio = st.Page(home_page, title="Home", icon="🏠", default=True)
    pagina_salas = st.Page(salas_page, title="Salas", icon="🏢")
    pagina_detalhes_sala = st.Page(detalhes_sala_page, title="Detalhes da Sala", icon="🔎")
    pagina_reservar = st.Page(reservar_page, title="Reservar Sala", icon="📅")
    pagina_minhas_reservas = st.Page(minhas_reservas_page, title="Minhas Reservas", icon="📋")

    st.session_state["pagina_reservar"] = pagina_reservar

    pages = [
        pagina_inicio,
        pagina_salas,
        pagina_detalhes_sala,
        pagina_reservar,
        pagina_minhas_reservas,
    ]

    navigation = st.navigation(pages)

    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {
            background-color: #0d1b3d;
        }
        section[data-testid="stSidebar"] * {
            color: #ffffff;
        }
        a[data-testid="stSidebarNavLink"] span[label] {
            font-size: 1.2rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.image("assets/logo_larptech_transparente.png", width=120)
        st.markdown(
            f"""
            <div style="background-color:#3a3a3a;color:white;padding:10px;border-radius:8px;">
            {usuario.role} : {usuario.nome}
            </div>
            <div style="height:16px;"></div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Sair"):
            logout_sessao()
            st.rerun()

    navigation.run()