import streamlit as st
from app.models.dados import carregar_salas
from app.utils.sessao import usuario_logado
from app.utils.salas_ocultas import ocultar_sala, esta_oculta


def formatar_nome_sala(nome):
    letras = []
    for i, caractere in enumerate(nome):
        if caractere.isdigit() and i > 0 and nome[i - 1].isalpha():
            letras.append(" ")
        letras.append(caractere)
    return "".join(letras)


def render():
    st.title("Salas")

    usuario = usuario_logado()
    eh_admin = usuario is not None and usuario.role == "Admin"

    salas = carregar_salas()
    salas = salas[~salas["idSala"].apply(esta_oculta)]

    predios_formatados = sorted(set(salas["predio"].apply(formatar_nome_sala)))

    st.subheader("Filtros")
    col1, col2, col3 = st.columns(3)
    with col1:
        somente_disponiveis = st.checkbox("Somente disponíveis")
    with col2:
        capacidade_minima = st.number_input("Capacidade mínima", min_value=0, value=0, step=1)
    with col3:
        predio_escolhido = st.selectbox("Prédio", ["Todos"] + predios_formatados)

    if somente_disponiveis:
        salas = salas[salas["status"] == "Disponivel"]
    if capacidade_minima:
        salas = salas[salas["capacidade"] >= capacidade_minima]
    if predio_escolhido != "Todos":
        salas = salas[salas["predio"].apply(formatar_nome_sala) == predio_escolhido]

    st.write(f"{len(salas)} sala(s) encontrada(s)")

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
                if st.button("Ver detalhes", key=f"detalhes_{sala['idSala']}"):
                    st.session_state["sala_pre_selecionada_detalhes"] = sala["idSala"]
                    st.switch_page(st.session_state["pagina_detalhes_sala"])
                if eh_admin:
                    if st.button("Ocultar", key=f"ocultar_{sala['idSala']}", type="primary"):
                        ocultar_sala(sala["idSala"])
                        st.rerun()