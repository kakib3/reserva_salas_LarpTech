import streamlit as st


@st.cache_resource
def _obter_conjunto_ocultas():
    return set()


def ocultar_sala(id_sala):
    _obter_conjunto_ocultas().add(id_sala)


def mostrar_sala(id_sala):
    _obter_conjunto_ocultas().discard(id_sala)


def esta_oculta(id_sala):
    return id_sala in _obter_conjunto_ocultas()


def listar_ocultas():
    return _obter_conjunto_ocultas()