"""sala_service contra um MySQL de verdade."""
import datetime as dt

import pytest

from app.services import sala_service


# ---- escrita ---------------------------------------------------------------
def test_admin_cria_sala_com_valores_de_enum_do_banco(banco, id_admin):
    resultado = sala_service.criar_sala("Sala10", 25, "BlocoA", "2", "Disponivel", "Sala", id_admin)

    assert resultado is not False
    linha = banco.um("SELECT * FROM salas WHERE nome = %s", ("Sala10",))
    assert linha["capacidade"] == 25
    assert linha["status_sala"] == "Disponivel"
    assert linha["tipo_sala"] == "Sala"


def test_criar_sala_exige_admin_e_valida_dados(banco, id_aluno, id_admin):
    with pytest.raises(PermissionError):
        sala_service.criar_sala("Sala10", 25, "BlocoA", "2", "Disponivel", "Sala", id_aluno)

    with pytest.raises(ValueError):
        sala_service.criar_sala("Sala10", 25, "BlocoA", "2", "Quebrada", "Sala", id_admin)

    with pytest.raises(ValueError):
        sala_service.criar_sala("Sala10", 0, "BlocoA", "2", "Disponivel", "Sala", id_admin)

    assert banco.contar("salas") == 0


def test_alterar_sala_persiste_e_preserva_o_status(banco, id_admin, criar_sala_db):
    id_sala = criar_sala_db("Sala", status="Manutencao")

    resultado = sala_service.alterar_sala(id_sala, "Sala77", 40, "BlocoB", "3", "Reuniao", id_admin)

    assert resultado is not False
    linha = banco.um("SELECT * FROM salas WHERE id_sala = %s", (id_sala,))
    assert (linha["nome"], linha["capacidade"], linha["predio"], linha["andar"], linha["tipo_sala"]) == (
        "Sala77", 40, "BlocoB", "3", "Reuniao")
    assert linha["status_sala"] == "Manutencao"


def test_alterar_sala_inexistente_retorna_false(id_admin):
    assert sala_service.alterar_sala(9999, "Sala77", 40, "BlocoB", "3", "Sala", id_admin) is False


def test_alterar_status_sala(banco, id_admin, id_sala):
    assert sala_service.alterar_status_sala(id_sala, "Manutencao", id_admin) is not False
    assert banco.um("SELECT status_sala FROM salas WHERE id_sala = %s", (id_sala,))["status_sala"] == "Manutencao"

    # mesmo status, sala inexistente e status inválido
    assert sala_service.alterar_status_sala(id_sala, "Manutencao", id_admin) is False
    assert sala_service.alterar_status_sala(9999, "Disponivel", id_admin) is False
    with pytest.raises(ValueError):
        sala_service.alterar_status_sala(id_sala, "Quebrada", id_admin)


# ---- consultas -------------------------------------------------------------
def test_sala_oculta_so_aparece_para_admin(id_admin, id_aluno, criar_sala_db):
    visivel = criar_sala_db("Sala", nome="Visivel")
    oculta = criar_sala_db("Sala", nome="Oculta")
    sala_service.ocultar_sala(oculta, id_admin)

    nomes_aluno = [s["nome"] for s in sala_service.consultar_salas(id_aluno)]
    salas_admin = {s["nome"]: s for s in sala_service.consultar_salas(id_admin)}

    assert nomes_aluno == ["Visivel"]
    assert set(salas_admin) == {"Visivel", "Oculta"}
    assert salas_admin["Oculta"]["oculta"] is True
    assert sala_service.consultar_disponibilidade(oculta, dt.date.today(), id_aluno) is None


def test_filtros_de_consulta(id_aluno, criar_sala_db):
    criar_sala_db("Sala", nome="Grande", capacidade=60)
    criar_sala_db("Sala", nome="Pequena", capacidade=10)
    criar_sala_db("Sala", nome="Quebrada", capacidade=60, status="Manutencao")

    assert {s["nome"] for s in sala_service.consultar_salas(id_aluno, capacidade_minima=50)} == {"Grande", "Quebrada"}
    assert {s["nome"] for s in sala_service.consultar_salas(id_aluno, somente_disponiveis=True)} == {"Grande", "Pequena"}
    assert {s["nome"] for s in sala_service.consultar_salas_disponiveis(limite=5)} == {"Grande", "Pequena"}


def test_disponibilidade_le_colunas_time_e_ignora_canceladas(id_aluno, id_sala, segunda, criar_reserva_db):
    criar_reserva_db(id_aluno, id_sala, segunda, "08:00:00", "09:00:00", "Confirmada")
    criar_reserva_db(id_aluno, id_sala, segunda, "10:00:00", "11:00:00", "Pendente")
    criar_reserva_db(id_aluno, id_sala, segunda, "13:00:00", "14:00:00", "Cancelada")

    resultado = sala_service.consultar_disponibilidade(id_sala, segunda, id_aluno)

    assert resultado["reservavel"] is True
    assert [r["hora_inicio"] for r in resultado["reservas"]] == [dt.time(8, 0), dt.time(10, 0)]
    assert [r["status_reserva"] for r in resultado["reservas"]] == ["Confirmada", "Pendente"]
    assert resultado["horarios_livres"] == [
        (dt.time(7, 0), dt.time(8, 0)),
        (dt.time(9, 0), dt.time(10, 0)),
        (dt.time(11, 0), dt.time(22, 0)),
    ]


def test_disponibilidade_de_sala_em_manutencao_nao_tem_horarios_livres(id_aluno, criar_sala_db, segunda):
    id_sala = criar_sala_db("Sala", status="Manutencao")

    resultado = sala_service.consultar_disponibilidade(id_sala, segunda, id_aluno)

    assert resultado["reservavel"] is False
    assert resultado["horarios_livres"] == []
