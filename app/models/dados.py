import pandas as pd
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

def carregar_usuarios():
    arquivo = DATA_DIR / "usuarios.csv"
    return pd.read_csv(arquivo, sep=";")

def carregar_salas():
    arquivo = DATA_DIR / "salas.csv"
    return pd.read_csv(arquivo, sep=";")

def carregar_equipamentos():
    arquivo = DATA_DIR / "equipamentos.csv"
    return pd.read_csv(arquivo, sep=";")

def carregar_reservas():
    arquivo = DATA_DIR / "reservas.csv"
    return pd.read_csv(arquivo, sep=";")

def obter_equipamentos_da_sala(id_sala):
    arquivo = DATA_DIR / "sala_equipamento.csv"
    sala_equipamento = pd.read_csv(arquivo, sep=";")    
    return sala_equipamento[sala_equipamento["idSala"] == id_sala]

def obter_reservas_da_sala(id_sala, data = None):
    arquivo = DATA_DIR / "reservas.csv"
    reservas = pd.read_csv(arquivo, sep=";")
    
    if data is not None:
        return reservas[(reservas["idSala"] == id_sala) & (reservas["data"] == data)]
    
    return reservas[reservas["idSala"] == id_sala]

# Até aqui todas as funções apenas retornam um dataframe.

def verificar_conflito(id_sala, data, hora_inicio, hora_fim): # Essa função só verifica conflitos.
    arquivo = DATA_DIR / "reservas.csv"
    reservas = pd.read_csv(arquivo, sep=";")
 
    mesma_sala_e_data = (
        (reservas["idSala"] == id_sala)
        & (reservas["data"] == data) 
        & (reservas["status"] == "Confirmada")
    )
    sobreposicao = (reservas["horaInicio"] < hora_fim) & (reservas["horaFim"] > hora_inicio)
    
    return not reservas[mesma_sala_e_data & sobreposicao].empty

def criar_reserva(id_usuario, id_sala, data, hora_inicio, hora_fim):
    arquivo = DATA_DIR / "reservas.csv"

    if ( verificar_conflito(id_sala, data, hora_inicio, hora_fim) ):
        return False # Verifica se há um conflito. Se houver conflito, a função termina e o front deve exibir
                     #a mensagem de erro correspondente.
                     
    df_existente = pd.read_csv(arquivo, sep=";")
    novo_id = int(df_existente["idReserva"].max()) + 1 if not df_existente.empty else 1
    nova_reserva = pd.DataFrame(
        [
            {
                "idReserva": novo_id,
                "idUser": id_usuario,
                "idSala": id_sala,
                "data": data,
                "horaInicio": hora_inicio,
                "horaFim": hora_fim,
                "status": "Confirmada",
                "criado_em": date.today().isoformat(),
            }
        ]
    )

    df_atualizado = pd.concat(
        [df_existente, nova_reserva], ignore_index=True
    )
    df_atualizado.to_csv(arquivo, sep=";", index=False)
    return novo_id

def cancelar_reserva(id_reserva):
    arquivo = DATA_DIR / "reservas.csv"
    df = pd.read_csv(arquivo, sep=";")

    filtro = df["idReserva"] == id_reserva
    
    if not filtro.any(): 
        return False # Checa se há uma reserva correspondente. Se não houver, a função termina.
                     # O front deve exibir a mensagem de erro correspondente.

    df.loc[filtro, "status"] = "Cancelada"

    df.to_csv(arquivo, sep=";", index=False)
    return True

def alterar_reserva(id_reserva, nova_sala, nova_data, novo_inicio, novo_fim):
    arquivo = DATA_DIR / "reservas.csv"
    df = pd.read_csv(arquivo, sep=";")
    
    
    if ( verificar_conflito(nova_sala, nova_data, novo_inicio, novo_fim) ):
        return False # Novamente, checa conflito. Mensagem de erro no front.
    
    filtro = df["idReserva"] == id_reserva
    
    if not filtro.any(): 
            return False

    df.loc[filtro, "idSala"] = nova_sala
    df.loc[filtro, "data"] = nova_data
    df.loc[filtro, "horaInicio"] = novo_inicio
    df.loc[filtro, "horaFim"] = novo_fim
    
    df.to_csv(arquivo, sep=";", index=False)
    
    return True
