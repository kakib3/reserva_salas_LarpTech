import streamlit as st
from app.controllers import usuarios_controller
from app.models.constantes import StatusUsuario
from app.models.usuario import Usuario
from app.utils import mensagens
from app.utils.sessao import usuario_logado


def render():
    st.title("Gerenciar Usuários")
    mensagens.exibir()

    usuario = usuario_logado()

    if usuario is None or not usuario.eh_admin:
        st.warning("Apenas administradores podem gerenciar usuários.")
        return

    aba_cadastrar, aba_editar = st.tabs(["Cadastrar usuário", "Editar usuário"])

    with aba_cadastrar:
        _formulario_cadastro(usuario)

    with aba_editar:
        _formulario_edicao(usuario)


def _mostrar_erros_de_validacao(nome, email, telefone, perfil, senha=None):
    """Mostra todos os erros do formulário de uma vez. Retorna True se está tudo válido."""
    valido, _, erros = usuarios_controller.validar_dados_usuario(nome, email, telefone, perfil, senha)
    for erro in erros:
        st.error(erro)
    return valido


def _formulario_cadastro(usuario):
    versao_form = st.session_state.get("versao_form_cadastro_usuario", 0)

    with st.form(f"form_cadastrar_usuario_{versao_form}"):
        nome = st.text_input("Nome completo")

        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("E-mail")
            perfil = st.selectbox("Perfil", Usuario.ROLES_VALIDAS)
        with col2:
            telefone = st.text_input("Telefone", placeholder="DDD + número")
            senha = st.text_input("Senha", type="password")

        enviado = st.form_submit_button("Cadastrar usuário", type="primary")

    if enviado:
        nome, email, telefone = nome.strip(), email.strip(), telefone.strip()

        if not _mostrar_erros_de_validacao(nome, email, telefone, perfil, senha):
            return

        sucesso, mensagem, _ = usuarios_controller.cadastrar_usuario(
            nome, email, telefone, perfil, senha, usuario.id
        )
        if sucesso:
            mensagens.agendar("sucesso", mensagem)
            st.session_state["versao_form_cadastro_usuario"] = versao_form + 1  # limpa o formulário
            st.rerun()
        else:
            st.error(mensagem)


def _formulario_edicao(usuario):
    sucesso, mensagem, usuarios = usuarios_controller.listar_todos_usuarios(usuario.id)

    if not sucesso:
        st.error(mensagem)
        return

    if not usuarios:
        st.info("Nenhum usuário cadastrado ainda.")
        return

    usuarios_por_id = {u["id_usuario"]: u for u in usuarios}

    def descrever(id_escolhido):
        u = usuarios_por_id[id_escolhido]
        return f"{u['nome']} ({u['email']})"

    id_usuario = st.selectbox("Escolha o usuário", list(usuarios_por_id), format_func=descrever)
    selecionado = usuarios_por_id[id_usuario]
    perfil_atual = selecionado["papel"]
    indice_perfil = Usuario.ROLES_VALIDAS.index(perfil_atual) if perfil_atual in Usuario.ROLES_VALIDAS else 0
    inativo = selecionado["status_usuario"] == StatusUsuario.INATIVO

    with st.form(f"form_editar_usuario_{id_usuario}"):
        nome = st.text_input("Nome completo", value=selecionado["nome"])

        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("E-mail", value=selecionado["email"])
            perfil = st.selectbox("Perfil", Usuario.ROLES_VALIDAS, index=indice_perfil)
        with col2:
            telefone = st.text_input("Telefone", value=str(selecionado["telefone"] or ""))
            st.text_input(
                "Status",
                value=selecionado["status_usuario"],
                disabled=True,
                key=f"status_{id_usuario}_{selecionado['status_usuario']}",
            )

        col_salvar, col_desativar = st.columns([4, 1])
        with col_salvar:
            salvar = st.form_submit_button("Salvar alterações", type="primary")
        with col_desativar:
            desativar = st.form_submit_button("Desativar", disabled=inativo)

    if salvar:
        nome, email, telefone = nome.strip(), email.strip(), telefone.strip()

        if not _mostrar_erros_de_validacao(nome, email, telefone, perfil):
            return

        sucesso, mensagem, _ = usuarios_controller.editar_usuario(
            id_usuario, nome, email, telefone, perfil, usuario.id
        )
        _finalizar_edicao(sucesso, mensagem)

    if desativar:
        sucesso, mensagem, _ = usuarios_controller.desativar_usuario(id_usuario, usuario.id)
        _finalizar_edicao(sucesso, mensagem)


def _finalizar_edicao(sucesso, mensagem):
    if sucesso:
        mensagens.agendar("sucesso", mensagem)
        st.rerun()
    else:
        st.error(mensagem)
