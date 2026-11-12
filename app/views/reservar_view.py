import streamlit as st
from datetime import date, time
from app.models.dados import carregar_salas
from app.controllers.reservas_controller import reservar_sala
from app.utils.sessao import usuario_logado
from app.utils.salas_ocultas import esta_oculta
from app.utils.formatacao import formatar_nome_sala


def render():
    st.title("Reservar Sala")
    usuario = usuario_logado()

    salas = [sala for sala in carregar_salas() if not esta_oculta(sala["id_sala"])]

    if not salas:
        st.info("Nenhuma sala disponível para reserva.")
        return

    nomes_formatados = [formatar_nome_sala(sala["nome"]) for sala in salas]
    ids_salas = [sala["id_sala"] for sala in salas]

    if "sala_pre_selecionada" in st.session_state:
        sala_pre_selecionada = st.session_state.pop("sala_pre_selecionada")
        if sala_pre_selecionada in ids_salas:
            st.session_state["indice_sala_reservar"] = ids_salas.index(sala_pre_selecionada)

    if st.session_state.get("indice_sala_reservar", 0) >= len(salas):
        st.session_state["indice_sala_reservar"] = 0

    indice_escolhido = st.selectbox(
        "Seleção da Sala",
        range(len(nomes_formatados)),
        format_func=lambda i: nomes_formatados[i],
        key="indice_sala_reservar",
    )
    id_sala = ids_salas[indice_escolhido]

    data_reserva = st.date_input(
        "Data da reserva",
        min_value=date.today(),
        format="DD/MM/YYYY",
    )
    hora_inicio = st.time_input("Horário de início", value=time(8, 0))
    hora_fim = st.time_input("Horário de término", value=time(9, 0))

    if st.button("Confirmar reserva"):
        sucesso, mensagem, reserva = reservar_sala(
            usuario.id, id_sala, data_reserva, hora_inicio, hora_fim
        )
        if sucesso and "pendente" in mensagem.lower():
            st.info(mensagem)
        elif sucesso:
            st.success(mensagem)
        else:
            st.error(mensagem)