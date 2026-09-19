import pandas as pd
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

def carregar_usuarios():
    arquivo = DATA_DIR / "usuarios.csv"
    return pd.read_csv(arquivo, sep=";", dtype={"senha": str, "telefone": str})

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
