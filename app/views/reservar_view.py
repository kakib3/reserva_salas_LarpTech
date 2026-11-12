import streamlit as st
from datetime import date, time
from app.controllers import reservas_controller, salas_controller
from app.utils.sessao import usuario_logado
from app.utils.formatacao import formatar_nome_sala


def render():
    st.title("Reservar Sala")

    usuario = usuario_logado()

    sucesso, mensagem, salas = (
        salas_controller.consultar_salas_para_reserva(
            usuario.id
        )
    )

    if not sucesso:
        st.error(mensagem)
        return

    if not salas:
        st.info("Nenhuma sala disponível para reserva.")
        return

    # Recupera a sala selecionada na tela anterior
    sala_pre_selecionada = st.session_state.pop(
        "sala_pre_selecionada", None
    )

    ids_salas = [sala["id_sala"] for sala in salas]

    if sala_pre_selecionada in ids_salas:
        st.session_state["indice_sala_reservar"] = (
            ids_salas.index(sala_pre_selecionada)
        )

    if "indice_sala_reservar" not in st.session_state:
        st.session_state["indice_sala_reservar"] = 0

    indice_escolhido = st.selectbox(
        "Seleção da Sala",
        range(len(salas)),
        format_func=lambda i: formatar_nome_sala(
            salas[i]["nome"]
        ),
        key="indice_sala_reservar"
    )

    id_sala = salas[indice_escolhido]["id_sala"]

    data_reserva = st.date_input(
        "Data da reserva",
        min_value=date.today(),
        format="DD/MM/YYYY"
    )

    hora_inicio = st.time_input(
        "Horário de início",
        value=time(8, 0)
    )

    hora_fim = st.time_input(
        "Horário de término",
        value=time(9, 0)
    )

    if st.button("Confirmar reserva"):
        sucesso, mensagem, reserva = (
            reservas_controller.reservar_sala(
                usuario.id,
                id_sala,
                data_reserva,
                hora_inicio,
                hora_fim
            )
        )

        if sucesso and reserva.esta_pendente:
            st.info(mensagem)

        elif sucesso:
            st.success(mensagem)

        else:
            st.error(mensagem)