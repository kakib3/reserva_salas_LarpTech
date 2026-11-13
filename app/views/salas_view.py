import streamlit as st
from app.controllers import salas_controller
from app.utils.sessao import usuario_logado
from app.utils.formatacao import formatar_nome_sala


def render():
    st.title("Salas")

    usuario = usuario_logado()

    # Consulta dos prédios disponíveis para o filtro
    sucesso, mensagem, predios = (
        salas_controller.consultar_predios(usuario.id)
    )

    if not sucesso:
        st.error(mensagem)
        return

    st.subheader("Filtros")

    col1, col2, col3 = st.columns(3)

    with col1:
        somente_disponiveis = st.checkbox(
            "Somente disponíveis"
        )

    with col2:
        capacidade_minima = st.number_input(
            "Capacidade mínima",
            min_value=0,
            value=0,
            step=1
        )

    with col3:
        predio_escolhido = st.selectbox(
            "Prédio",
            ["Todos"] + predios
        )

    # Consulta já filtrada pelo service
    sucesso, mensagem, salas = (
        salas_controller.consultar_salas(
            id_usuario=usuario.id,
            somente_disponiveis=somente_disponiveis,
            capacidade_minima=capacidade_minima,
            predio=predio_escolhido
        )
    )

    if not sucesso:
        st.error(mensagem)
        return

    st.write(f"{len(salas)} sala(s) encontrada(s)")

    if not salas:
        st.write("Nenhuma sala encontrada com esses filtros.")
        return

    colunas = st.columns(2)

    for indice, sala in enumerate(salas):
        coluna_atual = colunas[indice % 2]

        with coluna_atual:
            with st.container(border=True):
                nome_sala = formatar_nome_sala(sala["nome"])

                st.write(nome_sala)
                st.write(f"Capacidade: {sala['capacidade']}")
                st.write(f"Status: {sala['status_sala']}")

                if sala["oculta"]:
                    st.caption("Oculta para os usuários")

                else:
                    if st.button(
                        "Ver detalhes",
                        key=f"detalhes_{sala['id_sala']}"
                    ):
                        st.session_state[
                            "sala_pre_selecionada_detalhes"
                        ] = sala["id_sala"]

                        st.switch_page(
                            st.session_state["pagina_detalhes_sala"]
                        )

                if sala["pode_gerenciar"]:
                    if sala["oculta"]:
                        if st.button(
                            "Exibir",
                            key=f"exibir_{sala['id_sala']}"
                        ):
                            sucesso, mensagem, _ = (
                                salas_controller.mostrar_sala(
                                    sala["id_sala"], usuario.id
                                )
                            )

                            if sucesso:
                                st.rerun()
                            else:
                                st.error(mensagem)

                    else:
                        if st.button(
                            "Ocultar",
                            key=f"ocultar_{sala['id_sala']}",
                            type="primary"
                        ):
                            sucesso, mensagem, _ = (
                                salas_controller.ocultar_sala(
                                    sala["id_sala"], usuario.id
                                )
                            )

                            if sucesso:
                                st.rerun()
                            else:
                                st.error(mensagem)