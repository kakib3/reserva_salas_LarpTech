import streamlit as st
from datetime import date, time
from app.models.dados import carregar_salas
from app.controllers.reservas_controller import reservar_sala


def formatar_nome_sala(nome):
    letras = []
    for i, caractere in enumerate(nome):
        if caractere.isdigit() and i > 0 and nome[i - 1].isalpha():
            letras.append(" ")
        letras.append(caractere)
    return "".join(letras)


def render():
    st.title("Reservar Sala")
    usuario = st.session_state["usuario_logado"]

    salas = carregar_salas()
    nomes_formatados = salas["nome"].apply(formatar_nome_sala).tolist()

    indice_escolhido = st.selectbox(
        "Seleção da Sala",
        range(len(nomes_formatados)),
        format_func=lambda i: nomes_formatados[i],
    )
    id_sala = salas.iloc[indice_escolhido]["idSala"]

    data_reserva = st.date_input("Data da reserva", min_value=date.today())
    hora_inicio = st.time_input("Horário de início", value=time(8, 0))
    hora_fim = st.time_input("Horário de término", value=time(9, 0))

    if st.button("Confirmar reserva"):
        sucesso, mensagem, reserva = reservar_sala(
            usuario["idUser"], id_sala, data_reserva, hora_inicio, hora_fim
        )
        if sucesso and "pendente" in mensagem.lower():
            st.info(mensagem)
        elif sucesso:
            st.success(mensagem)
        else:
            st.error(mensagem)