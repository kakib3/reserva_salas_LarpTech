import streamlit as st
from app.models.dados import carregar_salas


def formatar_nome_sala(nome):
    letras = []
    for i, caractere in enumerate(nome):
        if caractere.isdigit() and i > 0 and nome[i - 1].isalpha():
            letras.append(" ")
        letras.append(caractere)
    return "".join(letras)


def render():
    st.title("Salas")

    st.subheader("Filtros")
    col1, col2, col3 = st.columns(3)
    with col1:
        somente_disponiveis = st.checkbox("Somente disponíveis")
    with col2:
        capacidade_minima = st.number_input("Capacidade minima", min_value=0, value=0, step=1)
    with col3:
        predio = st.text_input("Predio")

    salas = carregar_salas()

    if somente_disponiveis:
        salas = salas[salas["status"] == "Disponivel"]
    if capacidade_minima:
        salas = salas[salas["capacidade"] >= capacidade_minima]
    if predio:
        salas = salas[salas["predio"].str.contains(predio, case=False, na=False)]

    if salas.empty:
        st.write("Nenhuma sala encontrada com esses filtros.")
        return

    colunas = st.columns(2)
    for indice, (_, sala) in enumerate(salas.iterrows()):
        coluna_atual = colunas[indice % 2]
        with coluna_atual:
            with st.container(border=True):
                st.write(formatar_nome_sala(sala["nome"]))
                st.write(f"Capacidade: {sala['capacidade']}")
                st.write(f"Status: {sala['status']}")