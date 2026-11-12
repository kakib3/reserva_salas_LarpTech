import streamlit as st
from datetime import date, time, datetime, timedelta
from app.models.dados import carregar_salas, obter_reservas_da_sala, carregar_usuarios
from app.utils.salas_ocultas import esta_oculta
from app.utils.formatacao import formatar_nome_sala, formatar_hora
from app.models.constantes import StatusReserva, StatusSala


def converter_para_time(valor):
    if isinstance(valor, timedelta):
        return (datetime.min + valor).time()
    return valor


def render():
    st.title("Detalhes da Sala")

    salas = [sala for sala in carregar_salas() if not esta_oculta(sala["id_sala"])]

    if not salas:
        st.info("Nenhuma sala cadastrada.")
        return

    sala_pre_selecionada = st.session_state.pop("sala_pre_selecionada_detalhes", None)
    ids_salas = [sala["id_sala"] for sala in salas]
    indice_padrao = 0
    if sala_pre_selecionada is not None and sala_pre_selecionada in ids_salas:
        indice_padrao = ids_salas.index(sala_pre_selecionada)

    sala = st.selectbox(
        "Selecione a sala",
        salas,
        index=indice_padrao,
        format_func=lambda s: formatar_nome_sala(s["nome"]),
    )

    st.subheader(formatar_nome_sala(sala["nome"]))
    st.write(f"Capacidade: {sala['capacidade']}")
    st.write(f"Prédio: {formatar_nome_sala(sala['predio'])} — Andar: {sala['andar']}")
    st.write(f"Status: {sala['status_sala']}")

    st.subheader("Consulta de disponibilidade")

    data_consulta = st.date_input(
        "Selecione uma data",
        value=date.today(),
        key="data_disponibilidade"
    )

    reservas = [
        reserva for reserva in obter_reservas_da_sala(sala["id_sala"], data_consulta)
        if reserva["status_reserva"] in StatusReserva.ATIVAS
    ]
    for reserva in reservas:
        reserva["hora_inicio"] = converter_para_time(reserva["hora_inicio"])
        reserva["hora_fim"] = converter_para_time(reserva["hora_fim"])
    reservas.sort(key=lambda reserva: reserva["hora_inicio"])

    st.write(f"Disponibilidade em: {data_consulta.strftime('%d/%m/%Y')}")

    if not reservas:
        st.info("Nenhuma reserva registrada para esta data.")
    else:
        nomes_usuarios = {u["id_usuario"]: u["nome"] for u in carregar_usuarios()}

        tabela = [
            {
                "Usuário": nomes_usuarios.get(reserva["id_usuario"], "Desconhecido"),
                "Início": formatar_hora(reserva["hora_inicio"]),
                "Fim": formatar_hora(reserva["hora_fim"]),
                "Status": reserva["status_reserva"],
            }
            for reserva in reservas
        ]

        st.write("**Horários ocupados:**")
        st.dataframe(tabela, hide_index=True)

    if sala["status_sala"] != StatusSala.DISPONIVEL:
        st.warning("Esta sala não está disponível para novas reservas.")
    else:
        abertura = time(7, 0)
        fechamento = time(22, 0)

        horario_atual = abertura
        horarios_livres = []

        for reserva in reservas:
            inicio = reserva["hora_inicio"]
            fim = reserva["hora_fim"]

            if inicio > horario_atual:
                duracao = (
                    (inicio.hour * 60 + inicio.minute)
                    - (horario_atual.hour * 60 + horario_atual.minute)
                )

                if duracao >= 30:
                    horarios_livres.append((horario_atual, inicio))

            if fim > horario_atual:
                horario_atual = fim

        if horario_atual < fechamento:
            duracao = (
                (fechamento.hour * 60 + fechamento.minute)
                - (horario_atual.hour * 60 + horario_atual.minute)
            )

            if duracao >= 30:
                horarios_livres.append((horario_atual, fechamento))

        st.write("**Horários livres:**")

        if horarios_livres:
            for inicio, fim in horarios_livres:
                st.success(
                    f"{inicio.strftime('%H:%M')} às "
                    f"{fim.strftime('%H:%M')}"
                )
        else:
            st.warning("Não existem horários livres nesta data.")