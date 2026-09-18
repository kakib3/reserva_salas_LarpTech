import streamlit as st

from app.views.home_view import render as render_home
from app.views.salas_view import render as render_salas
from app.views.detalhes_sala_view import render as render_detalhes_sala
from app.views.reservar_view import render as render_reservar
from app.views.minhas_reservas_view import render as render_minhas_reservas


from app.models.dados import carregar_usuarios


if "usuario_logado" not in st.session_state:
    usuarios = carregar_usuarios()
    st.session_state["usuario_logado"] = usuarios.iloc[0].to_dict()


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


pages = [
    st.Page(home_page, title="Início", icon="🏠", default=True),
    st.Page(salas_page, title="Salas", icon="🏢"),
    st.Page(detalhes_sala_page, title="Detalhes da Sala", icon="🔎"),
    st.Page(reservar_page, title="Reservar", icon="📅"),
    st.Page(minhas_reservas_page, title="Minhas Reservas", icon="📋"),
]

navigation = st.navigation(pages)

navigation.run()