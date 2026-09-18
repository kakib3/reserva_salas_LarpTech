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


pagina_inicio = st.Page(home_page, title="Início", icon="🏠", default=True)
pagina_salas = st.Page(salas_page, title="Salas", icon="🏢")
pagina_detalhes_sala = st.Page(detalhes_sala_page, title="Detalhes da Sala", icon="🔎")
pagina_reservar = st.Page(reservar_page, title="Reservar", icon="📅")
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
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.image("assets/logo_larptech.png", width=120)

with st.sidebar:
    usuario = st.session_state["usuario_logado"]
    st.markdown(
        f"""
        <div style="background-color:#3a3a3a;color:white;padding:10px;border-radius:8px;">
        {usuario['role']} : {usuario['nome']}
        </div>
        """,
        unsafe_allow_html=True,
    )

navigation.run()