import streamlit as st
from app.controllers import usuarios_controller
from app.models.usuario import Usuario
from app.utils.sessao import usuario_logado


def render():
    st.title("Gerenciar Usuários")

    usuario = usuario_logado()

    if usuario is None or usuario.role != "Admin":
        st.warning("Apenas administradores podem gerenciar usuários.")
        return

    aba_cadastrar, aba_editar = st.tabs(["Cadastrar usuário", "Editar usuário"])

    with aba_cadastrar:
        _formulario_cadastro(usuario)

    with aba_editar:
        _formulario_edicao(usuario)


def _validar_campos(nome, email, telefone, perfil, senha=None):
    novo_usuario = Usuario(None, nome, email, telefone, perfil, senha)
    validacoes = [
        novo_usuario.validar_nome,
        novo_usuario.validar_email,
        novo_usuario.validar_telefone,
        novo_usuario.validar_role,
    ]
    if senha is not None:
        validacoes.append(novo_usuario.validar_senha)

    erros = []
    for validar in validacoes:
        try:
            validar()
        except ValueError as e:
            erros.append(str(e))
    return erros


def _formulario_cadastro(usuario):
    mensagem_sucesso = st.session_state.pop("cadastro_usuario_sucesso", None)
    if mensagem_sucesso:
        st.success(mensagem_sucesso)

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

        erros = _validar_campos(nome, email, telefone, perfil, senha)
        if erros:
            for erro in erros:
                st.error(erro)
            return

        sucesso, mensagem, _ = usuarios_controller.cadastrar_usuario(
            nome, email, telefone, perfil, senha, usuario.id
        )
        if sucesso:
            st.session_state["cadastro_usuario_sucesso"] = mensagem
            st.session_state["versao_form_cadastro_usuario"] = versao_form + 1
            st.rerun()
        else:
            st.error(mensagem)


def _formulario_edicao(usuario):
    mensagem_sucesso = st.session_state.pop("edicao_usuario_sucesso", None)
    if mensagem_sucesso:
        st.success(mensagem_sucesso)

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
    inativo = selecionado["status_usuario"] == "Inativo"

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

        erros = _validar_campos(nome, email, telefone, perfil)
        if erros:
            for erro in erros:
                st.error(erro)
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
        st.session_state["edicao_usuario_sucesso"] = mensagem
        st.rerun()
    else:
        st.error(mensagem)