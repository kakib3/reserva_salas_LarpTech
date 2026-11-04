import streamlit as st

class StatusReserva:
    CONFIRMADA = "Confirmada"
    PENDENTE = "Pendente"
    CANCELADA = "Cancelada"
    
    ATIVAS = (CONFIRMADA, PENDENTE)
    
class StatusSala:
    DISPONIVEL = "Disponivel"
    MANUTENCAO = "Manutencao"
    INDISPONIVEL = "Indisponivel"
    
class TipoSala:
    SALA = "SALA"
    REUNIAO = "REUNIAO"
    LABORATORIO = "LABORATORIO"
    AUDITORIO = "AUDITORIO"
    
    PRECISA_APROVACAO = (LABORATORIO, AUDITORIO)