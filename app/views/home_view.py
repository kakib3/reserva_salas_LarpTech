import streamlit as st
from datetime import date
from app.models.dados import carregar_salas, carregar_reservas, carregar_usuarios
from app.controllers.reservas_controller import aprovar_reserva, negar_reserva
from app.utils.sessao import usuario_logado
from app.utils.salas_ocultas import esta_oculta


def formatar_nome_sala(nome):
    letras = []
    for i, caractere in enumerate(nome):
        if caractere.isdigit() and i > 0 and nome[i - 1].isalpha():
            letras.append(" ")
        letras.append(caractere)
    return "".join(letras)


def render():
    usuario = usuario_logado()

    st.title("LarpReserve")
    st.write(f"Bem-vindo, {usuario.nome}")
    st.write(date.today().strftime("%d/%m/%Y"))

    col_reserva, col_disponiveis = st.columns(2)

    with col_reserva:
        st.subheader("Próxima reserva")
        salas = carregar_salas().set_index("idSala")
        reservas = carregar_reservas()
        minhas = reservas[reservas["idUser"] == usuario.id]
        minhas = minhas[minhas["status"].isin(["Confirmada", "Pendente"])]

        if minhas.empty:
            st.write("Você não tem nenhuma reserva agendada.")
        else:
            proxima = minhas.sort_values(by=["data", "horaInicio"]).iloc[0]
            if proxima["idSala"] in salas.index:
                nome_sala = formatar_nome_sala(salas.loc[proxima["idSala"], "nome"])
            else:
                nome_sala = proxima["idSala"]

            with st.container(border=True):
                st.write(nome_sala)
                st.write(f"Data: {proxima['data']}")
                st.write(f"Hora: {proxima['horaInicio']} às {proxima['horaFim']}")
                st.write(f"Status: {proxima['status']}")

        if usuario.role == "Admin":
            st.subheader("Pendências")
            todas_reservas = carregar_reservas()
            pendentes = todas_reservas[todas_reservas["status"] == "Pendente"]

            if pendentes.empty:
                st.write("Nenhuma pendência no momento.")
            else:
                usuarios = carregar_usuarios().set_index("idUser")
                for _, pendencia in pendentes.iterrows():
                    if pendencia["idSala"] in salas.index:
                        nome_sala_pendencia = formatar_nome_sala(salas.loc[pendencia["idSala"], "nome"])
                    else:
                        nome_sala_pendencia = pendencia["idSala"]

                    if pendencia["idUser"] in usuarios.index:
                        solicitante = usuarios.loc[pendencia["idUser"]]
                        descricao_solicitante = f"{solicitante['role']} : {solicitante['nome']}"
                    else:
                        descricao_solicitante = "Usuário desconhecido"

                    with st.container(border=True):
                        st.write(f"{nome_sala_pendencia} - {descricao_solicitante}")
                        st.write(f"Data: {pendencia['data']}")
                        st.write(f"Hora: {pendencia['horaInicio']} às {pendencia['horaFim']}")

                        col_aprovar, col_negar = st.columns(2)
                        with col_aprovar:
                            if st.button("Reservar", key=f"aprovar_{pendencia['idReserva']}"):
                                sucesso, mensagem, _ = aprovar_reserva(pendencia["idReserva"])
                                if sucesso:
                                    st.success(mensagem)
                                    st.rerun()
                                else:
                                    st.error(mensagem)
                        with col_negar:
                            if st.button("Cancelar", key=f"negar_{pendencia['idReserva']}"):
                                sucesso, mensagem, _ = negar_reserva(pendencia["idReserva"])
                                if sucesso:
                                    st.success(mensagem)
                                    st.rerun()
                                else:
                                    st.error(mensagem)

    with col_disponiveis:
        st.subheader("Salas disponíveis agora")
        salas_disponiveis = carregar_salas()
        salas_disponiveis = salas_disponiveis[~salas_disponiveis["idSala"].apply(esta_oculta)]
        disponiveis = salas_disponiveis[salas_disponiveis["status"] == "Disponivel"]

        if disponiveis.empty:
            st.write("Nenhuma sala disponível no momento.")
        else:
            for _, sala in disponiveis.head(5).iterrows():
                with st.container(border=True):
                    st.write(formatar_nome_sala(sala["nome"]))
                    st.write(f"Prédio: {formatar_nome_sala(sala['predio'])}")
                    st.write(f"Capacidade: {sala['capacidade']}")
                    st.write(f"Status: {sala['status']}")
                    if st.button("Reservar", key=f"reservar_{sala['idSala']}"):
                        st.session_state["sala_pre_selecionada"] = sala["idSala"]
                        st.switch_page(st.session_state["pagina_reservar"])