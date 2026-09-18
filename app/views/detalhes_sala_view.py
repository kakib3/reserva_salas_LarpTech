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

    indice_escolhido = st.selectbox(
        "Selecione a sala",
        range(len(nomes_formatados)),
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