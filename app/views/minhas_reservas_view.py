import streamlit as st
from datetime import datetime
from app.models.dados import carregar_reservas, carregar_salas
from app.controllers.reservas_controller import cancelar_reserva, alterar_reserva
from app.utils.sessao import usuario_logado


def formatar_nome_sala(nome):
    letras = []
    for i, caractere in enumerate(nome):
        if caractere.isdigit() and i > 0 and nome[i - 1].isalpha():
            letras.append(" ")
        letras.append(caractere)
    return "".join(letras)


def converter_data(texto):
    return datetime.strptime(str(texto), "%d/%m/%Y").date()


def converter_hora(texto):
    texto = str(texto)
    if texto.count(":") == 2:
        return datetime.strptime(texto, "%H:%M:%S").time()
    return datetime.strptime(texto, "%H:%M").time()


def render():
    st.title("Minhas Reservas")
    usuario = usuario_logado()

    reservas = carregar_reservas()
    minhas_reservas = reservas[reservas["idUser"] == usuario.id]

    if minhas_reservas.empty:
        st.write("Você ainda não tem nenhuma reserva.")
        return

    salas = carregar_salas().set_index("idSala")

    for _, reserva in minhas_reservas.iterrows():
        if reserva["idSala"] in salas.index:
            nome_sala = formatar_nome_sala(salas.loc[reserva["idSala"], "nome"])
        else:
            nome_sala = reserva["idSala"]

        with st.container(border=True):
            st.write(nome_sala)
            st.write(f"Data: {reserva['data']}")
            st.write(f"Hora: {reserva['horaInicio']} às {reserva['horaFim']}")
            st.write(f"Status: {reserva['status']}")

            if reserva["status"] in ["Confirmada", "Pendente"]:
                col_cancelar, col_alterar = st.columns(2)

                with col_cancelar:
                    if st.button("Cancelar", key=f"cancelar_{reserva['idReserva']}"):
                        sucesso, mensagem, _ = cancelar_reserva(reserva["idReserva"], usuario.id)
                        if sucesso:
                            st.success(mensagem)
                            st.rerun()
                        else:
                            st.error(mensagem)

                with col_alterar:
                    with st.popover("Alterar"):
                        nova_data = st.date_input(
                            "Nova data",
                            value=converter_data(reserva["data"]),
                            format="DD/MM/YYYY",
                            key=f"data_{reserva['idReserva']}",
                        )
                        novo_inicio = st.time_input(
                            "Novo horário de início",
                            value=converter_hora(reserva["horaInicio"]),
                            key=f"inicio_{reserva['idReserva']}",
                        )
                        novo_fim = st.time_input(
                            "Novo horário de término",
                            value=converter_hora(reserva["horaFim"]),
                            key=f"fim_{reserva['idReserva']}",
                        )
                        if st.button("Salvar alteração", key=f"salvar_{reserva['idReserva']}"):
                            sucesso, mensagem, _ = alterar_reserva(
                                reserva["idReserva"], usuario.id, reserva["idSala"], nova_data, novo_inicio, novo_fim
                            )
                            if sucesso:
                                st.success(mensagem)
                                st.rerun()
                            else:
                                st.error(mensagem)