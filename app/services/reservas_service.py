import pandas as pd

from app.models.dados import DATA_DIR
from app.models.reserva import Reserva
from datetime import date


def carregar_salas():
    arquivo = DATA_DIR / "salas.csv"
    return pd.read_csv(arquivo, sep=";")


def verificar_sala_disponivel(id_sala):
    salas = from app.models.dados import carregar_salas

    sala = salas[salas["idSala"] == id_sala]

    if sala.empty:
        return False

    return sala.iloc[0]["status"] == "Disponivel"

def verificar_conflito_horario(id_sala, data, hora_inicio, hora_fim, id_reserva_ignorar=None):
    arquivo = DATA_DIR / "reservas.csv"
    reservas = pd.read_csv(arquivo, sep=";")
    
    reservas["data"] = pd.to_datetime(
        reservas["data"],
        format="%d/%m/%Y"
    ).dt.date
    
    reservas["horaInicio"] = pd.to_datetime(
        reservas["horaInicio"],
        format="mixed"
    ).dt.time

    reservas["horaFim"] = pd.to_datetime(
        reservas["horaFim"],
        format="mixed"
    ).dt.time

    mesma_sala_e_data = (
        (reservas["idSala"] == id_sala)
        & (reservas["data"] == data) 
        & (reservas["status"].isin(["Confirmada", "Pendente"]))
    )
    sobreposicao = (reservas["horaInicio"] < hora_fim) & (reservas["horaFim"] > hora_inicio)

    if id_reserva_ignorar is not None:
        mesma_sala_e_data &= reservas["idReserva"] != id_reserva_ignorar

    return not reservas[mesma_sala_e_data & sobreposicao].empty

def criar_reserva(id_usuario, id_sala, data, hora_inicio, hora_fim):
    arquivo = DATA_DIR / "reservas.csv"
    
    if not verificar_sala_disponivel(id_sala):
        return False  # Sala indisponível
    
    reserva_obj = Reserva(None, id_usuario, id_sala, data, hora_inicio, hora_fim, None, None)
    
    reserva_obj.validar_horario()
    reserva_obj.validar_intervalo()
    reserva_obj.validar_horario_funcionamento()
    reserva_obj.validar_dia_util()
    
    if verificar_conflito_horario(id_sala, data, hora_inicio, hora_fim):
        return False  # Conflito de horário
    
    sala_tipo = descobre_tipo_sala(id_sala)
    
    if(sala_tipo == "LABORATORIO" or sala_tipo == "AUDITORIO"):
        reserva_obj.status = "Pendente"
    elif(sala_tipo == "SALA" or sala_tipo == "REUNIAO"):
        reserva_obj.status = "Confirmada"
        
    reservas = pd.read_csv(arquivo, sep=";")
    novo_id = reservas["idReserva"].max() + 1 if not reservas.empty else 1
    reserva_obj.criado_em = date.today()
    reserva_obj.id = novo_id
    
    nova_reserva = {
    "idReserva": reserva_obj.id,
    "idUser": reserva_obj.usuario_id,
    "idSala": reserva_obj.sala_id,
    "data": reserva_obj.data.strftime("%d/%m/%Y"),
    "horaInicio": reserva_obj.hora_inicio.strftime("%H:%M"),
    "horaFim": reserva_obj.hora_fim.strftime("%H:%M"),
    "status": reserva_obj.status,
    "criado_em": reserva_obj.criado_em.strftime("%d/%m/%Y"),
    }
    
    nova_linha = pd.DataFrame([nova_reserva])
    reservas = pd.concat([reservas, nova_linha], ignore_index=True)
    reservas.to_csv(arquivo, sep=";", index=False)
    return reserva_obj

def cancelar_reserva(id_reserva,id_usuario):
    arquivo = DATA_DIR / "reservas.csv"
    reservas = pd.read_csv(arquivo, sep=";")
    
    reserva = reservas[reservas["idReserva"] == id_reserva]
    
    if reserva.empty:
        return False  # Reserva não encontrada
    
    if reserva.iloc[0]["idUser"] != id_usuario:
        return False  # Usuário não autorizado a cancelar esta reserva
    
    if reserva.iloc[0]["status"] not in ["Confirmada", "Pendente"]:
        return False 
    
    reservas.loc[reservas["idReserva"] == id_reserva, "status"] = "Cancelada"
    reservas.to_csv(arquivo, sep=";", index=False)
    return True

def alterar_reserva(id_reserva, id_usuario, nova_sala, nova_data, novo_inicio, novo_fim):
    arquivo = DATA_DIR / "reservas.csv"
    reservas = pd.read_csv(arquivo, sep=";")
    
    reserva = reservas[reservas["idReserva"] == id_reserva]
    
    if reserva.empty:
        return False  # Reserva não encontrada
    
    if reserva.iloc[0]["idUser"] != id_usuario:
        return False  # Usuário não autorizado a alterar esta reserva
    
    if reserva.iloc[0]["status"] not in ["Confirmada", "Pendente"]:
        return False  # Reserva não pode ser alterada
    
    if not verificar_sala_disponivel(nova_sala):
        return False  # Sala indisponível
    
    reserva_obj = Reserva(id_reserva, id_usuario, nova_sala, nova_data, novo_inicio, novo_fim, reserva.iloc[0]["status"], None)
    
    reserva_obj.validar_horario()
    reserva_obj.validar_intervalo()
    reserva_obj.validar_horario_funcionamento()
    reserva_obj.validar_dia_util()
    
    if verificar_conflito_horario(nova_sala, nova_data, novo_inicio, novo_fim, id_reserva_ignorar=id_reserva):
        return False  # Conflito de horário
    
    sala_tipo = descobre_tipo_sala(nova_sala)
    
    if(sala_tipo == "LABORATORIO" or sala_tipo == "AUDITORIO"):
        reserva_obj.status = "Pendente"
    elif(sala_tipo == "SALA" or sala_tipo == "REUNIAO"):
        reserva_obj.status = "Confirmada"
    
    reservas.loc[reservas["idReserva"] == id_reserva, ["idSala", "data", "horaInicio", "horaFim", "status"]] = [nova_sala, nova_data.strftime("%d/%m/%Y"), novo_inicio.strftime("%H:%M"), novo_fim.strftime("%H:%M"), reserva_obj.status]
    
    reservas.to_csv(arquivo, sep=";", index=False)
    return True

#Métodos Utilitários
def descobre_tipo_sala(id_sala):
    salas = from app.models.dados import carregar_salas
    sala = salas[salas["idSala"] == id_sala]
    if not sala.empty:
        return sala.iloc[0]["tipoSala"]
    return None
