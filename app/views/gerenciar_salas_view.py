import streamlit as st
from app.controllers import salas_controller
from app.models.sala import Sala
from app.models.constantes import StatusSala
from app.utils.sessao import usuario_logado
from app.utils.formatacao import formatar_nome_sala


def render():
    st.title("Gerenciar Salas")

    usuario = usuario_logado()

    if usuario is None or usuario.role != "Admin":
        st.warning("Apenas administradores podem gerenciar salas.")
        return

    aba_cadastrar, aba_editar = st.tabs(["Cadastrar sala", "Editar sala"])

    with aba_cadastrar:
        _formulario_cadastro(usuario)

    with aba_editar:
        _formulario_edicao(usuario)


def _formulario_cadastro(usuario):
    with st.form("form_cadastrar_sala", clear_on_submit=True):
        nome = st.text_input("Nome da sala", placeholder="Ex.: Sala05")

        col1, col2 = st.columns(2)
        with col1:
            tipo_sala = st.selectbox("Tipo", Sala.TIPOS_VALIDOS)
            predio = st.text_input("Prédio", placeholder="Ex.: Anexo1")
        with col2:
            capacidade = st.number_input("Capacidade", min_value=1, value=1, step=1)
            andar = st.number_input("Andar", min_value=0, value=0, step=1)

        status = st.selectbox(
            "Status",
            Sala.STATUS_VALIDOS,
            index=Sala.STATUS_VALIDOS.index(StatusSala.DISPONIVEL),
        )

        enviado = st.form_submit_button("Cadastrar sala", type="primary")

    if enviado:
        if not predio.strip():
            st.error("Informe o prédio da sala.")
            return

        sucesso, mensagem, _ = salas_controller.cadastrar_sala(
            nome.strip(), int(capacidade), predio.strip(), int(andar),
            status, tipo_sala, usuario.id,
        )
        if sucesso:
            st.success(mensagem)
        else:
            st.error(mensagem)


def _formulario_edicao(usuario):
    salas = salas_controller.listar_todas_salas()

    if not salas:
        st.info("Nenhuma sala cadastrada ainda.")
        return

    def descrever(sala):
        return f"{formatar_nome_sala(sala['nome'])} ({sala['predio']})"

    sala = st.selectbox("Escolha a sala", salas, format_func=descrever)
    id_sala = sala["id_sala"]

    with st.form(f"form_editar_sala_{id_sala}"):
        nome = st.text_input("Nome da sala", value=sala["nome"])

        tipo_atual = sala["tipo_sala"]
        indice_tipo = Sala.TIPOS_VALIDOS.index(tipo_atual) if tipo_atual in Sala.TIPOS_VALIDOS else 0

        col1, col2 = st.columns(2)
        with col1:
            tipo_sala = st.selectbox("Tipo", Sala.TIPOS_VALIDOS, index=indice_tipo)
            predio = st.text_input("Prédio", value=str(sala["predio"] or ""))
        with col2:
            capacidade = st.number_input(
                "Capacidade", min_value=1, value=max(1, int(sala["capacidade"])), step=1
            )
            andar = st.number_input(
                "Andar", min_value=0, value=int(sala["andar"] or 0), step=1
            )

        salvar = st.form_submit_button("Salvar alterações", type="primary")

    if salvar:
        if not predio.strip():
            st.error("Informe o prédio da sala.")
        else:
            sucesso, mensagem, _ = salas_controller.editar_sala(
                id_sala, nome.strip(), int(capacidade), predio.strip(), int(andar),
                tipo_sala, usuario.id,
            )
            if sucesso:
                st.success(mensagem)
            else:
                st.error(mensagem)

    st.subheader("Status da sala")
    st.write(f"Status atual: **{sala['status_sala']}**")

    col_status, col_botao = st.columns([3, 1], vertical_alignment="bottom")
    with col_status:
        novo_status = st.selectbox(
            "Novo status", Sala.STATUS_VALIDOS, key=f"novo_status_{id_sala}"
        )
    with col_botao:
        alterar = st.button("Alterar status", key=f"alterar_status_{id_sala}")

    if alterar:
        sucesso, mensagem, _ = salas_controller.mudar_status_sala(
            id_sala, novo_status, usuario.id
        )
        if sucesso:
            st.success(mensagem)
        else:
            st.error(mensagem)