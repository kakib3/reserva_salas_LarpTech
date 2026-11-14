import pytest

from app.models.usuario import Usuario


def _usuario(senha):
    return Usuario(None, "Ana Silva", "ana@teste.com", "92 99999-9999", "Aluno", senha)


@pytest.mark.parametrize("senha", ["Senha123", "abcdefg1", "1234567a", "Senha@123", "a" * 70 + "12"])
def test_aceita_senha_forte(senha):
    _usuario(senha).validar_senha()


@pytest.mark.parametrize("senha", ["", "abc1", "Ab1", "1234567"])
def test_recusa_senha_com_menos_de_8_caracteres(senha):
    with pytest.raises(ValueError, match="pelo menos 8"):
        _usuario(senha).validar_senha()


@pytest.mark.parametrize("senha", ["somenteletras", "12345678"])
def test_recusa_senha_sem_letra_ou_sem_numero(senha):
    with pytest.raises(ValueError, match="uma letra e um número"):
        _usuario(senha).validar_senha()


@pytest.mark.parametrize("senha", [None, 12345678, ["Senha123"]])
def test_recusa_senha_que_nao_e_texto(senha):
    with pytest.raises(ValueError):
        _usuario(senha).validar_senha()


def test_recusa_senha_acima_do_limite_de_72_bytes_do_bcrypt():
    with pytest.raises(ValueError, match="no máximo 72"):
        _usuario("a1" * 37).validar_senha()


def test_limite_de_bytes_considera_acentos():
    # 40 caracteres, mas 78 bytes em UTF-8.
    with pytest.raises(ValueError, match="no máximo 72"):
        _usuario("é" * 38 + "a1").validar_senha()
