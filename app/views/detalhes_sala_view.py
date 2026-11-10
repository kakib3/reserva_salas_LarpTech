import streamlit as st
import pandas as pd
from app.models.dados import carregar_salas, obter_reservas_da_sala, carregar_usuarios
from app.utils.salas_ocultas import esta_oculta
from app.utils.formatacao import formatar_nome_sala
from app.models.constantes import StatusReserva
from datetime import date, time

def render():
    st.title("Detalhes da Sala")

    salas = carregar_salas()
    salas = salas[~salas["idSala"].apply(esta_oculta)]
    nomes_formatados = salas["nome"].apply(formatar_nome_sala).tolist()

    sala_pre_selecionada = st.session_state.pop("sala_pre_selecionada_detalhes", None)
    ids_salas = salas["idSala"].tolist()
    indice_padrao = 0
    if sala_pre_selecionada is not None and sala_pre_selecionada in ids_salas:
        indice_padrao = ids_salas.index(sala_pre_selecionada)

    indice_escolhido = st.selectbox(
        "Selecione a sala",
        range(len(nomes_formatados)),
        index=indice_padrao,
        format_func=lambda i: nomes_formatados[i],
    )
    sala = salas.iloc[indice_escolhido]

    st.subheader(formatar_nome_sala(sala["nome"]))
    st.write(f"Capacidade: {sala['capacidade']}")
    st.write(f"Prédio: {formatar_nome_sala(sala['predio'])} — Andar: {sala['andar']}")
    st.write(f"Status: {sala['status']}")
    
    st.subheader("Consulta de disponibilidade")
    
    # Seleciona a data para consultar os horários
    data_consulta = st.date_input(
        "Selecione uma data",
        value=date.today(),
        key="data_disponibilidade"
    )

    # Busca todas as reservas da sala selecionada
    reservas = obter_reservas_da_sala(sala["idSala"])

    # Reservas confirmadas e pendentes ocupam horários
    reservas = reservas[
        reservas["status"].isin(StatusReserva.ATIVAS)
    ].copy()

    # Converte os formatos de data e horário
    if not reservas.empty:
        reservas["data"] = pd.to_datetime(
            reservas["data"],
            format="%d/%m/%Y"
        ).dt.date

        reservas["horaInicio"] = pd.to_datetime(
            reservas["horaInicio"],
            format="mixed"
        ).dt.time

        reservas["horaFim"] = pd.to_datetime(
            reservas["horaFim"],
            format="mixed"
        ).dt.time

    # Filtra as reservas da data escolhida
    reservas = reservas[
        reservas["data"] == data_consulta
    ].sort_values("horaInicio")

    st.write(f"Disponibilidade em: {data_consulta.strftime('%d/%m/%Y')}")

    # Exibe as reservas ocupadas
    if reservas.empty:
        st.info("Nenhuma reserva registrada para esta data.")
    else:
        usuarios = carregar_usuarios()

        reservas_com_usuarios = reservas.merge(
            usuarios[["idUser", "nome"]],
            on="idUser",
            how="left"
        )

        tabela = reservas_com_usuarios[
            ["nome", "horaInicio", "horaFim", "status"]
        ].rename(columns={
            "nome": "Usuário",
            "horaInicio": "Início",
            "horaFim": "Fim",
            "status": "Status"
        })

        st.write("**Horários ocupados:**")
        st.dataframe(tabela, hide_index=True)

    # Calcula os intervalos livres
    if sala["status"] != "Disponivel":
        st.warning(
            "Esta sala não está disponível para novas reservas."
        )
    else:
        abertura = time(7, 0)
        fechamento = time(22, 0)

        horario_atual = abertura
        horarios_livres = []

        for _, reserva in reservas.iterrows():
            inicio = reserva["horaInicio"]
            fim = reserva["horaFim"]

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