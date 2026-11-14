import pytest

from app.utils.seguranca import gerar_hash_senha, verificar_senha


def test_hash_nao_guarda_a_senha_em_texto():
    hash_gerado = gerar_hash_senha("Senha@123")

    assert hash_gerado != "Senha@123"
    assert hash_gerado.startswith("$2")


def test_mesma_senha_gera_hashes_diferentes_por_causa_do_salt():
    assert gerar_hash_senha("Senha@123") != gerar_hash_senha("Senha@123")


def test_verificar_aceita_a_senha_correta():
    hash_gerado = gerar_hash_senha("Senha@123")

    assert verificar_senha("Senha@123", hash_gerado) is True


def test_verificar_recusa_senha_errada():
    hash_gerado = gerar_hash_senha("Senha@123")

    assert verificar_senha("Senha@124", hash_gerado) is False


def test_verificar_recusa_senha_antiga_em_texto_puro_sem_lancar_erro():
    assert verificar_senha("1234", "1234") is False


@pytest.mark.parametrize("senha, hash_armazenado", [
    (None, "$2b$12$abc"),
    ("Senha@123", None),
    (123456, "$2b$12$abc"),
])
def test_verificar_recusa_tipos_invalidos(senha, hash_armazenado):
    assert verificar_senha(senha, hash_armazenado) is False


@pytest.mark.parametrize("senha", ["", None, 123])
def test_gerar_hash_recusa_senha_invalida(senha):
    with pytest.raises(ValueError):
        gerar_hash_senha(senha)
