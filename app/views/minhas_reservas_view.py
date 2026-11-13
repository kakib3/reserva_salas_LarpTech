import streamlit as st
from app.controllers import reservas_controller
from app.utils.sessao import usuario_logado


def render():
    st.title("Minhas Reservas")

    usuario = usuario_logado()

    sucesso, mensagem, minhas_reservas = (
        reservas_controller.consultar_reservas_usuario(
            usuario.id
        )
    )

    if not sucesso:
        st.error(mensagem)
        return

    if not minhas_reservas:
        st.write("Você ainda não tem nenhuma reserva.")
        return

    for reserva in minhas_reservas:
        with st.container(border=True):
            st.write(reserva["nome_sala"])
            st.write(f"Data: {reserva['data_reserva']}")
            st.write(
                f"Hora: {reserva['hora_inicio']} às "
                f"{reserva['hora_fim']}"
            )
            st.write(f"Status: {reserva['status_reserva']}")

            if reserva["pode_alterar"]:
                col_cancelar, col_alterar = st.columns(2)

                with col_cancelar:
                    if st.button(
                        "Cancelar",
                        key=f"cancelar_{reserva['id_reserva']}"
                    ):
                        sucesso, mensagem, _ = (
                            reservas_controller.cancelar_reserva(
                                reserva["id_reserva"],
                                usuario.id
                            )
                        )

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
                            key=f"data_{reserva['id_reserva']}"
                        )

                        novo_inicio = st.time_input(
                            "Novo horário de início",
                            value=reserva["hora_inicio"],
                            key=f"inicio_{reserva['id_reserva']}"
                        )

                        novo_fim = st.time_input(
                            "Novo horário de término",
                            value=reserva["hora_fim"],
                            key=f"fim_{reserva['id_reserva']}"
                        )

                        if st.button(
                            "Salvar alteração",
                            key=f"salvar_{reserva['id_reserva']}"
                        ):
                            sucesso, mensagem, _ = (
                                reservas_controller.alterar_reserva(
                                    reserva["id_reserva"],
                                    usuario.id,
                                    reserva["id_sala"],
                                    nova_data,
                                    novo_inicio,
                                    novo_fim
                                )
                            )

                            if sucesso:
                                st.success(mensagem)
                                st.rerun()
                            else:
                                st.error(mensagem)