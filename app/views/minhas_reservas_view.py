import streamlit as st
from datetime import datetime, timedelta
from app.models.dados import carregar_reservas, carregar_salas
from app.controllers.reservas_controller import cancelar_reserva, alterar_reserva
from app.utils.sessao import usuario_logado
from app.utils.formatacao import formatar_nome_sala, formatar_data, formatar_hora
from app.models.constantes import StatusReserva


def converter_para_time(valor):
    if isinstance(valor, timedelta):
        return (datetime.min + valor).time()
    return valor


def render():
    st.title("Minhas Reservas")
    usuario = usuario_logado()

    minhas_reservas = [
        reserva for reserva in carregar_reservas()
        if reserva["id_usuario"] == usuario.id
    ]

    if not minhas_reservas:
        st.write("Você ainda não tem nenhuma reserva.")
        return

    nomes_salas = {sala["id_sala"]: formatar_nome_sala(sala["nome"]) for sala in carregar_salas()}

    for reserva in minhas_reservas:
        id_reserva = reserva["id_reserva"]
        nome_sala = nomes_salas.get(reserva["id_sala"], reserva["id_sala"])

        with st.container(border=True):
            st.write(nome_sala)
            st.write(f"Data: {formatar_data(reserva['data_reserva'])}")
            st.write(f"Hora: {formatar_hora(reserva['hora_inicio'])} às {formatar_hora(reserva['hora_fim'])}")
            st.write(f"Status: {reserva['status_reserva']}")

            if reserva["status_reserva"] in StatusReserva.ATIVAS:
                col_cancelar, col_alterar = st.columns(2)

                with col_cancelar:
                    if st.button("Cancelar", key=f"cancelar_{id_reserva}"):
                        sucesso, mensagem, _ = cancelar_reserva(id_reserva, usuario.id)
                        if sucesso:
                            st.success(mensagem)
                            st.rerun()
                        else:
                            st.error(mensagem)

                with col_alterar:
                    with st.popover("Alterar"):
                        nova_data = st.date_input(
                            "Nova data",
                            value=reserva["data_reserva"],
                            format="DD/MM/YYYY",
                            key=f"data_{id_reserva}",
                        )
                        novo_inicio = st.time_input(
                            "Novo horário de início",
                            value=converter_para_time(reserva["hora_inicio"]),
                            key=f"inicio_{id_reserva}",
                        )
                        novo_fim = st.time_input(
                            "Novo horário de término",
                            value=converter_para_time(reserva["hora_fim"]),
                            key=f"fim_{id_reserva}",
                        )
                        if st.button("Salvar alteração", key=f"salvar_{id_reserva}"):
                            sucesso, mensagem, _ = alterar_reserva(
                                id_reserva, usuario.id, reserva["id_sala"], nova_data, novo_inicio, novo_fim
                            )
                            if sucesso:
                                st.success(mensagem)
                                st.rerun()
                            else:
                                st.error(mensagem)