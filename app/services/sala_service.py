import pandas as pd

from app.models.dados import DATA_DIR, carregar_salas
from app.models.sala import Sala


def listar_salas():
    return carregar_salas()


def buscar_sala_por_id(id_sala):
    salas = carregar_salas()
    sala = salas[salas["idSala"] == id_sala]

    if sala.empty:
        return None

    sala = sala.iloc[0]
    return Sala(sala["idSala"], sala["nome"], sala["capacidade"], sala["predio"], sala["andar"], sala["status"], sala["tipoSala"])


def criar_sala(nome, capacidade, predio, andar, status, tipo_sala):
    arquivo = DATA_DIR / "salas.csv"

    sala_obj = Sala(None, nome, capacidade, predio, andar, status, tipo_sala)

    sala_obj.validar_nome()
    sala_obj.validar_capacidade()
    sala_obj.validar_status()
    sala_obj.validar_tipo_sala()

    salas = carregar_salas()
    novo_id = 1 if salas.empty else int(salas["idSala"].max()) + 1
    sala_obj.id = novo_id

    nova_sala = pd.DataFrame([{
        "idSala": sala_obj.id,
        "nome": sala_obj.nome,
        "capacidade": sala_obj.capacidade,
        "predio": sala_obj.predio,
        "andar": sala_obj.andar,
        "status": sala_obj.status,
        "tipoSala": sala_obj.tipo_sala,
    }])

    salas = pd.concat([salas, nova_sala], ignore_index=True)
    salas.to_csv(arquivo, sep=";", index=False)

    return sala_obj


def alterar_sala(id_sala, nome, capacidade, predio, andar, tipo_sala):
    arquivo = DATA_DIR / "salas.csv"
    salas = carregar_salas()

    sala_atual = salas[salas["idSala"] == id_sala]

    if sala_atual.empty:
        return False  # Sala não encontrada

    sala_obj = Sala(id_sala, nome, capacidade, predio, andar, sala_atual.iloc[0]["status"], tipo_sala)

    sala_obj.validar_nome()
    sala_obj.validar_capacidade()
    sala_obj.validar_tipo_sala()

    filtro = salas["idSala"] == id_sala
    salas.loc[filtro, ["nome", "capacidade", "predio", "andar", "tipoSala"]] = [nome, capacidade, predio, andar, tipo_sala]

    salas.to_csv(arquivo, sep=";", index=False)
    return sala_obj


def alterar_status_sala(id_sala, novo_status):
    arquivo = DATA_DIR / "salas.csv"
    salas = carregar_salas()

    if novo_status not in Sala.STATUS_VALIDOS:
        raise ValueError(f"Status inválido. Deve ser um dos: {', '.join(Sala.STATUS_VALIDOS)}.")

    filtro = salas["idSala"] == id_sala

    if not filtro.any():
        return False  # Sala não encontrada

    if salas.loc[filtro, "status"].iloc[0] == novo_status:
        return False  # Já está nesse status

    salas.loc[filtro, "status"] = novo_status
    salas.to_csv(arquivo, sep=";", index=False)
    return True

