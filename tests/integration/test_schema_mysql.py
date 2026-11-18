"""O que só o MySQL real garante (enums, chaves estrangeiras, UNIQUE) e a
consistência entre os limites das colunas e as validações em Python."""
import mysql.connector
import pytest

from app.services import sala_service, usuarios_service


# ---- garantias do banco ----------------------------------------------------
def test_enum_invalido_e_rejeitado(banco):
    with pytest.raises(mysql.connector.Error):
        banco.executar(
            """INSERT INTO salas (nome, capacidade, predio, andar, status_sala, tipo_sala)
               VALUES ('S1', 10, 'A', '1', 'Quebrada', 'Sala')"""
        )


def test_chave_estrangeira_impede_reserva_de_usuario_ou_sala_inexistente(banco, id_aluno, id_sala):
    sql = """INSERT INTO reservas (id_usuario, id_sala, data_reserva, hora_inicio,
                                   hora_fim, status_reserva, criado_em)
             VALUES (%s, %s, '2030-01-07', '08:00:00', '09:00:00', 'Confirmada', '2030-01-01')"""

    with pytest.raises(mysql.connector.Error):
        banco.executar(sql, (9999, id_sala))
    with pytest.raises(mysql.connector.Error):
        banco.executar(sql, (id_aluno, 9999))


def test_email_duplicado_e_barrado_pelo_unique(banco, id_aluno):
    with pytest.raises(mysql.connector.Error):
        banco.executar(
            """INSERT INTO usuarios (nome, email, telefone, papel, senha, status_usuario)
               VALUES ('Outro', 'aluno@teste.com', '69999990000', 'Aluno', 'x', 'Ativo')"""
        )


# ---- a validação conhece os limites do schema -----------------------------
# Antes de chegar ao MySQL, o valor fora do limite vira ValueError (mensagem clara
# para o usuário), em vez de um erro de banco genérico.
def test_nome_de_sala_com_mais_de_10_caracteres_e_validado(banco, id_admin):
    with pytest.raises(ValueError, match="no máximo 10"):
        sala_service.criar_sala("Sala-Muito-Longa", 20, "BlocoA", "1", "Disponivel", "Sala", id_admin)

    assert banco.contar("salas") == 0


def test_capacidade_acima_de_255_e_validada(banco, id_admin):
    with pytest.raises(ValueError, match="no máximo 255"):
        sala_service.criar_sala("Sala10", 300, "BlocoA", "1", "Disponivel", "Sala", id_admin)

    assert banco.contar("salas") == 0


def test_predio_e_andar_acima_de_15_caracteres_sao_validados(banco, id_admin):
    with pytest.raises(ValueError, match="prédio"):
        sala_service.criar_sala("Sala10", 20, "x" * 16, "1", "Disponivel", "Sala", id_admin)
    with pytest.raises(ValueError, match="andar"):
        sala_service.criar_sala("Sala10", 20, "BlocoA", "x" * 16, "Disponivel", "Sala", id_admin)

    assert banco.contar("salas") == 0


def test_telefone_formatado_e_normalizado_antes_de_gravar(banco):
    resultado = usuarios_service.criar_usuario(
        "Maria Silva", "maria@teste.com", "(69) 99999-0000", "Aluno", "Senha123"
    )

    assert resultado is not False
    assert banco.um("SELECT telefone FROM usuarios")["telefone"] == "69999990000"


def test_alterar_usuario_tambem_normaliza_o_telefone(banco, id_aluno):
    usuarios_service.alterar_usuario(
        id_aluno, id_aluno, "Aluno Teste", "aluno@teste.com", "(69) 98888-7777", "Aluno"
    )

    assert banco.um("SELECT telefone FROM usuarios WHERE id_usuario = %s", (id_aluno,))["telefone"] == "69988887777"
