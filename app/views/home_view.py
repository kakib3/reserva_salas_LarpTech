import streamlit as st
from datetime import date
from app.models.dados import carregar_salas, carregar_reservas, carregar_usuarios
from app.controllers.reservas_controller import aprovar_reserva, negar_reserva
from app.utils.sessao import usuario_logado
from app.utils.salas_ocultas import esta_oculta
from app.utils.formatacao import formatar_nome_sala, formatar_data, formatar_hora
from app.models.constantes import StatusSala, StatusReserva


def render():
    usuario = usuario_logado()

    st.title("LarpReserve")
    st.write(f"Bem-vindo, {usuario.nome}")
    hoje = date.today()
    st.write(hoje.strftime("%d/%m/%Y"))

    salas = carregar_salas()
    nomes_salas = {sala["id_sala"]: formatar_nome_sala(sala["nome"]) for sala in salas}
    reservas = carregar_reservas()

    col_reserva, col_disponiveis = st.columns(2)

    with col_reserva:
        st.subheader("Próxima reserva")
        minhas = [
            reserva for reserva in reservas
            if reserva["id_usuario"] == usuario.id
            and reserva["status_reserva"] in StatusReserva.ATIVAS
            and reserva["data_reserva"] >= hoje
        ]

        if not minhas:
            st.write("Você não tem nenhuma reserva agendada.")
        else:
            proxima = min(minhas, key=lambda reserva: (reserva["data_reserva"], reserva["hora_inicio"]))

            with st.container(border=True):
                st.write(nomes_salas.get(proxima["id_sala"], proxima["id_sala"]))
                st.write(f"Data: {formatar_data(proxima['data_reserva'])}")
                st.write(f"Hora: {formatar_hora(proxima['hora_inicio'])} às {formatar_hora(proxima['hora_fim'])}")
                st.write(f"Status: {proxima['status_reserva']}")

        if usuario.role == "Admin":
            st.subheader("Pendências")
            pendentes = [
                reserva for reserva in reservas
                if reserva["status_reserva"] == StatusReserva.PENDENTE
            ]

            if not pendentes:
                st.write("Nenhuma pendência no momento.")
            else:
                usuarios = {u["id_usuario"]: u for u in carregar_usuarios()}
                for pendencia in pendentes:
                    nome_sala_pendencia = nomes_salas.get(pendencia["id_sala"], pendencia["id_sala"])

                    solicitante = usuarios.get(pendencia["id_usuario"])
                    if solicitante is not None:
                        descricao_solicitante = f"{solicitante['papel']} : {solicitante['nome']}"
                    else:
                        descricao_solicitante = "Usuário desconhecido"

                    with st.container(border=True):
                        st.write(f"{nome_sala_pendencia} - {descricao_solicitante}")
                        st.write(f"Data: {formatar_data(pendencia['data_reserva'])}")
                        st.write(f"Hora: {formatar_hora(pendencia['hora_inicio'])} às {formatar_hora(pendencia['hora_fim'])}")

                        col_aprovar, col_negar = st.columns(2)
                        with col_aprovar:
                            if st.button("Reservar", key=f"aprovar_{pendencia['id_reserva']}"):
                                sucesso, mensagem, _ = aprovar_reserva(pendencia["id_reserva"], usuario.id)
                                if sucesso:
                                    st.success(mensagem)
                                    st.rerun()
                                else:
                                    st.error(mensagem)
                        with col_negar:
                            if st.button("Cancelar", key=f"negar_{pendencia['id_reserva']}"):
                                sucesso, mensagem, _ = negar_reserva(pendencia["id_reserva"], usuario.id)
                                if sucesso:
                                    st.success(mensagem)
                                    st.rerun()
                                else:
                                    st.error(mensagem)

    with col_disponiveis:
        st.subheader("Salas disponíveis agora")
        disponiveis = [
            sala for sala in salas
            if not esta_oculta(sala["id_sala"])
            and sala["status_sala"] == StatusSala.DISPONIVEL
        ]

        if not disponiveis:
            st.write("Nenhuma sala disponível no momento.")
        else:
            for sala in disponiveis[:5]:
                with st.container(border=True):
                    st.write(formatar_nome_sala(sala["nome"]))
                    st.write(f"Prédio: {formatar_nome_sala(sala['predio'])}")
                    st.write(f"Capacidade: {sala['capacidade']}")
                    st.write(f"Status: {sala['status_sala']}")
                    if st.button("Reservar", key=f"reservar_{sala['id_sala']}"):
                        st.session_state["sala_pre_selecionada"] = sala["id_sala"]
                        st.switch_page(st.session_state["pagina_reservar"])