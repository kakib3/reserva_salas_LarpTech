"""Mensagens que sobrevivem ao `st.rerun()`.

Um `st.success(...)` seguido de `st.rerun()` some antes de o usuário ver, porque a
página é redesenhada do zero. Em vez disso, a view agenda a mensagem e a próxima
renderização a exibe uma única vez, com `exibir()`.

    mensagens.agendar_resultado(sucesso, mensagem)
    st.rerun()
    ...
    mensagens.exibir()   # no início da render() da página
"""
import streamlit as st

CHAVE = "mensagens_agendadas"

_EXIBIDORES = {
    "sucesso": "success",
    "erro": "error",
    "aviso": "warning",
    "info": "info",
}


def agendar(tipo, texto):
    st.session_state.setdefault(CHAVE, []).append((tipo, texto))


def agendar_resultado(sucesso, texto):
    agendar("sucesso" if sucesso else "erro", texto)


def exibir():
    for tipo, texto in st.session_state.pop(CHAVE, []):
        getattr(st, _EXIBIDORES.get(tipo, "info"))(texto)
