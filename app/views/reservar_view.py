import streamlit as st
from datetime import date, time
from app.models.dados import carregar_salas
from app.controllers.reservas_controller import reservar_sala
from app.utils.sessao import usuario_logado


def formatar_nome_sala(nome):
    letras = []
    for i, caractere in enumerate(nome):
        if caractere.isdigit() and i > 0 and nome[i - 1].isalpha():
            letras.append(" ")
        letras.append(caractere)
    return "".join(letras)


def render():
    st.title("Reservar Sala")
    usuario = usuario_logado()

    salas = carregar_salas()
    nomes_formatados = salas["nome"].apply(formatar_nome_sala).tolist()

    if "sala_pre_selecionada" in st.session_state:
        sala_pre_selecionada = st.session_state.pop("sala_pre_selecionada")
        ids_salas = salas["idSala"].tolist()
        if sala_pre_selecionada in ids_salas:
            st.session_state["indice_sala_reservar"] = ids_salas.index(sala_pre_selecionada)

    if "indice_sala_reservar" not in st.session_state:
        st.session_state["indice_sala_reservar"] = 0

    indice_escolhido = st.selectbox(
        "Seleção da Sala",
        range(len(nomes_formatados)),
        format_func=lambda i: nomes_formatados[i],
        key="indice_sala_reservar",
    )
    id_sala = salas.iloc[indice_escolhido]["idSala"]

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