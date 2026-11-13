
import logging

from app.messaging.email_sender import enviar_email
from app.services import usuarios_service, sala_service


logger = logging.getLogger(__name__)


def enviar_notificacao(id_usuario: int, assunto: str, corpo: str) -> bool:
    """
    Busca o usuário e envia uma notificação por e-mail.
    """

    try:
        usuario = usuarios_service.buscar_usuario_por_id(id_usuario)

        if usuario is None:
            logger.warning("Usuário %s não encontrado.", id_usuario)
            return False

        if not usuario.email:
            logger.warning(
                "Usuário %s não possui e-mail cadastrado.",
                id_usuario
            )
            return False

        return enviar_email(
            destinatario=usuario.email,
            assunto=assunto,
            corpo=corpo
        )

    except Exception:
        logger.exception(
            "Erro ao preparar notificação para o usuário %s.",
            id_usuario
        )
        return False


def _notificar_reserva(reserva, assunto: str, situacao: str, orientacao: str) -> bool:
    """
    Monta os dados da reserva e encaminha a notificação.
    """

    sala = sala_service.buscar_sala_por_id(reserva.sala_id)

    if sala is None:
        logger.warning(
            "Sala %s não encontrada para a reserva %s.",
            reserva.sala_id,
            reserva.id
        )
        return False

    data = reserva.data.strftime("%d/%m/%Y") if hasattr(reserva.data, "strftime") else str(reserva.data)

    hora_inicio = reserva.hora_inicio.strftime("%H:%M") if hasattr(reserva.hora_inicio, "strftime") else str(reserva.hora_inicio)

    hora_fim = reserva.hora_fim.strftime("%H:%M") if hasattr(reserva.hora_fim, "strftime") else str(reserva.hora_fim)

    corpo = (
        "Olá!\n\n"
        "Confira as informações da sua reserva:\n\n"
        f"Reserva: {reserva.id}\n"
        f"Sala: {sala['nome']}\n"
        f"Prédio: {sala['predio']}\n"
        f"Andar: {sala['andar']}\n"
        f"Data: {data}\n"
        f"Horário: {hora_inicio} às {hora_fim}\n\n"
        f"Situação: {situacao}\n\n"
        f"{orientacao}\n\n"
        "Sistema de Reservas LarpTech"
    )

    return enviar_notificacao(
        id_usuario=reserva.usuario_id,
        assunto=assunto,
        corpo=corpo
    )


def notificar_reserva_confirmada(reserva) -> bool:
    return _notificar_reserva(
        reserva,
        "Reserva confirmada - LarpTech",
        "Confirmada",
        "Sua reserva foi confirmada com sucesso."
    )


def notificar_reserva_pendente(reserva) -> bool:
    return _notificar_reserva(
        reserva,
        "Solicitação de reserva recebida - LarpTech",
        "Pendente de aprovação",
        "Você receberá outro e-mail quando houver uma decisão."
    )


def notificar_reserva_aprovada(reserva) -> bool:
    return _notificar_reserva(
        reserva,
        "Reserva aprovada - LarpTech",
        "Aprovada",
        "Sua solicitação foi aprovada pelo administrador."
    )


def notificar_reserva_recusada(reserva) -> bool:
    return _notificar_reserva(
        reserva,
        "Reserva recusada - LarpTech",
        "Recusada",
        "Sua solicitação não foi aprovada pelo administrador."
    )