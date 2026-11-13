import streamlit as st
from datetime import date
from app.controllers import salas_controller
from app.utils.sessao import usuario_logado
from app.utils.formatacao import formatar_nome_sala


def render():
    st.title("Detalhes da Sala")

    usuario = usuario_logado()

    # Consulta das salas visíveis para o usuário
    sucesso, mensagem, salas = (
        salas_controller.consultar_salas(
            id_usuario=usuario.id
        )
    )

    if not sucesso:
        st.error(mensagem)
        return

    if not salas:
        st.info("Nenhuma sala disponível para consulta.")
        return

    sala_pre_selecionada = st.session_state.pop(
        "sala_pre_selecionada_detalhes", None
    )

    ids_salas = [sala["id_sala"] for sala in salas]

    indice_padrao = 0

    if sala_pre_selecionada in ids_salas:
        indice_padrao = ids_salas.index(sala_pre_selecionada)

    indice_escolhido = st.selectbox(
        "Selecione a sala",
        range(len(salas)),
        index=indice_padrao,
        format_func=lambda i: formatar_nome_sala(
            salas[i]["nome"]
        )
    )

    sala = salas[indice_escolhido]

    st.subheader(formatar_nome_sala(sala["nome"]))
    st.write(f"Capacidade: {sala['capacidade']}")
    st.write(
        f"Prédio: {formatar_nome_sala(sala['predio'])} "
        f"— Andar: {sala['andar']}"
    )
    st.write(f"Status: {sala['status_sala']}")

    st.subheader("Consulta de disponibilidade")

    data_consulta = st.date_input(
        "Selecione uma data",
        value=date.today(),
        key="data_disponibilidade"
    )

    # A consulta já retorna reservas e intervalos livres.
    sucesso, mensagem, disponibilidade = (
        salas_controller.consultar_disponibilidade(
            sala["id_sala"], data_consulta, usuario.id
        )
    )

    if not sucesso:
        st.error(mensagem)
        return

    st.write(
        f"Disponibilidade em: {data_consulta.strftime('%d/%m/%Y')}"
    )

    reservas = disponibilidade["reservas"]
    horarios_livres = disponibilidade["horarios_livres"]

    if not reservas:
        st.info("Nenhuma reserva registrada para esta data.")

    else:
        tabela = [
            {
                "Usuário": reserva["nome_usuario"],
                "Início": reserva["hora_inicio"],
                "Fim": reserva["hora_fim"],
                "Status": reserva["status_reserva"]
            }
            for reserva in reservas
        ]

        st.write("**Horários ocupados:**")
        st.dataframe(tabela, hide_index=True)

    if not disponibilidade["reservavel"]:
        st.warning(
            "Esta sala não está disponível para novas reservas."
        )

    else:
        st.write("**Horários livres:**")

        if horarios_livres:
            for inicio, fim in horarios_livres:
                st.success(f"{inicio} às {fim}")

        else:
            st.warning(
                "Não existem horários livres nesta data."
            )