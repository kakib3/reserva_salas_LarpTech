
import logging
import smtplib
import ssl
from email.message import EmailMessage

import streamlit as st


logger = logging.getLogger(__name__)


def enviar_email(destinatario: str, assunto: str, corpo: str) -> bool:
    """
    Envia um e-mail utilizando as configurações SMTP do Streamlit.

    Retorna True se o envio for concluído e False caso contrário.
    """

    # 1. Recupera as configurações
    try:
        config = st.secrets["email"]
    except Exception:
        logger.warning("Configurações de e-mail não encontradas.")
        return False

    servidor = config.get("smtp_server")
    porta = config.get("smtp_port")
    remetente = config.get("sender")
    senha = config.get("password")

    # 2. Verifica se todas as configurações necessárias existem
    if not all([servidor, porta, remetente, senha]):
        logger.warning("Configurações de e-mail incompletas.")
        return False

    # 3. Monta a mensagem
    mensagem = EmailMessage()
    mensagem["From"] = remetente
    mensagem["To"] = destinatario
    mensagem["Subject"] = assunto
    mensagem.set_content(corpo)

    # 4. Realiza o envio
    try:
        contexto = ssl.create_default_context()

        with smtplib.SMTP(servidor, int(porta)) as smtp:
            smtp.starttls(context=contexto)
            smtp.login(remetente, senha)
            smtp.send_message(mensagem)

        logger.info("E-mail enviado para %s.", destinatario)
        return True

    except Exception:
        logger.exception("Falha ao enviar e-mail para %s.", destinatario)
        return False
