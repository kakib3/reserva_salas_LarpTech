import streamlit as st
from datetime import date
from app.controllers import reservas_controller, salas_controller
from app.utils.sessao import usuario_logado


def render():
    usuario = usuario_logado()

    st.title("LarpReserve")
    st.write(f"Bem-vindo, {usuario.nome}")
    st.write(date.today().strftime("%d/%m/%Y"))

    col_reserva, col_disponiveis = st.columns(2)

    # Próxima reserva
    with col_reserva:
        st.subheader("Próxima reserva")

        sucesso, mensagem, proxima = (
            reservas_controller.consultar_proxima_reserva(
                usuario.id, date.today()
            )
        )

        if not sucesso:
            st.error(mensagem)
        elif proxima is None:
            st.write("Você não tem nenhuma reserva agendada.")
        else:
            with st.container(border=True):
                st.write(proxima["nome_sala"])
                st.write(
                    f"Data: {proxima['data_reserva']}"
                )
                st.write(
                    f"Hora: {proxima['hora_inicio']} às "
                    f"{proxima['hora_fim']}"
                )
                st.write(f"Status: {proxima['status_reserva']}")

        # Pendências administrativas
        sucesso, mensagem, pode_gerenciar = (
            reservas_controller.pode_gerenciar_pendencias(usuario.id)
        )

        if not sucesso:
            st.error(mensagem)

        elif pode_gerenciar:
            st.subheader("Pendências")

            sucesso, mensagem, pendentes = (
                reservas_controller.consultar_reservas_pendentes(usuario.id)
            )

            if not sucesso:
                st.error(mensagem)

            elif not pendentes:
                st.write("Nenhuma pendência no momento.")

            else:
                for pendencia in pendentes:
                    with st.container(border=True):
                        st.write(
                            f"{pendencia['nome_sala']} - "
                            f"{pendencia['papel']} : "
                            f"{pendencia['nome_usuario']}"
                        )
                        st.write(
                            f"Data: {pendencia['data_reserva']}"
                        )
                        st.write(
                            f"Hora: {pendencia['hora_inicio']} às "
                            f"{pendencia['hora_fim']}"
                        )

                        col_aprovar, col_negar = st.columns(2)

                        with col_aprovar:
                            if st.button(
                                "Reservar",
                                key=f"aprovar_{pendencia['id_reserva']}"
                            ):
                                sucesso, mensagem, _ = (
                                    reservas_controller.aprovar_reserva(
                                        pendencia["id_reserva"],
                                        usuario.id
                                    )
                                )

                                if sucesso:
                                    st.success(mensagem)
                                    st.rerun()
                                else:
                                    st.error(mensagem)

                        with col_negar:
                            if st.button(
                                "Cancelar",
                                key=f"negar_{pendencia['id_reserva']}"
                            ):
                                sucesso, mensagem, _ = (
                                    reservas_controller.negar_reserva(
                                        pendencia["id_reserva"],
                                        usuario.id
                                    )
                                )

                                if sucesso:
                                    st.success(mensagem)
                                    st.rerun()
                                else:
                                    st.error(mensagem)

    # Salas disponíveis
    with col_disponiveis:
        st.subheader("Salas disponíveis agora")

        sucesso, mensagem, salas = (
            salas_controller.consultar_salas_disponiveis(
                limite=5
            )
        )

        if not sucesso:
            st.error(mensagem)

        elif not salas:
            st.write("Nenhuma sala disponível no momento.")

        else:
            for sala in salas:
                with st.container(border=True):
                    st.write(sala["nome"])
                    st.write(f"Prédio: {sala['predio']}")
                    st.write(f"Capacidade: {sala['capacidade']}")
                    st.write(f"Status: {sala['status_sala']}")

                    if st.button(
                        "Reservar",
                        key=f"reservar_{sala['id_sala']}"
                    ):
                        st.session_state["sala_pre_selecionada"] = (
                            sala["id_sala"]
                        )
                        st.switch_page(
                            st.session_state["pagina_reservar"]
                        )