import streamlit as st
from app.models.dados import carregar_salas, obter_reservas_da_sala, carregar_usuarios


def formatar_nome_sala(nome):
    letras = []
    for i, caractere in enumerate(nome):
        if caractere.isdigit() and i > 0 and nome[i - 1].isalpha():
            letras.append(" ")
        letras.append(caractere)
    return "".join(letras)


def render():
    st.title("Detalhes da Sala")

    salas = carregar_salas()
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

    st.subheader("Reservas confirmadas")
    reservas = obter_reservas_da_sala(sala["idSala"])
    reservas = reservas[reservas["status"] == "Confirmada"]

    if reservas.empty:
        st.write("Nenhuma reserva confirmada para esta sala.")
    else:
        usuarios = carregar_usuarios()
        reservas = reservas.merge(usuarios, on="idUser", how="left")
        tabela = reservas[["nome", "data", "horaInicio", "horaFim"]].rename(
            columns={
                "nome": "Usuário",
                "data": "Data",
                "horaInicio": "Início",
                "horaFim": "Fim",
            }
        )
        st.dataframe(tabela, hide_index=True)