import streamlit as st
from app.models.dados import carregar_salas, carregar_reservas


def formatar_nome_sala(nome):
    letras = []
    for i, caractere in enumerate(nome):
        if caractere.isdigit() and i > 0 and nome[i - 1].isalpha():
            letras.append(" ")
        letras.append(caractere)
    return "".join(letras)


def render():
    usuario = st.session_state["usuario_logado"]

    st.title("LarpReserve")
    st.write(f"Bem-vindo, {usuario['nome']}")

    col_reserva, col_disponiveis = st.columns(2)

    with col_reserva:
        st.subheader("Próxima reserva")
        reservas = carregar_reservas()
        minhas = reservas[reservas["idUser"] == usuario["idUser"]]
        minhas = minhas[minhas["status"].isin(["Confirmada", "Pendente"])]

        if minhas.empty:
            st.write("Você não tem nenhuma reserva agendada.")
        else:
            proxima = minhas.sort_values(by=["data", "horaInicio"]).iloc[0]
            st.write(f"Data: {proxima['data']}")
            st.write(f"Hora: {proxima['horaInicio']} às {proxima['horaFim']}")

    with col_disponiveis:
        st.subheader("Salas disponíveis agora")
        salas = carregar_salas()
        disponiveis = salas[salas["status"] == "Disponivel"]

        if disponiveis.empty:
            st.write("Nenhuma sala disponível no momento.")
        else:
            for _, sala in disponiveis.head(5).iterrows():
                with st.container(border=True):
                    st.write(formatar_nome_sala(sala["nome"]))
                    if st.button("Reservar", key=f"reservar_{sala['idSala']}"):
                        st.session_state["sala_pre_selecionada"] = sala["idSala"]
                        st.switch_page(st.session_state["pagina_reservar"])