"""Limites das colunas do banco refletidos nas validações dos modelos."""
import pytest

from app.models.sala import Sala
from app.models.usuario import Usuario


def sala(**kw):
    dados = dict(id=None, nome="Sala01", capacidade=30, predio="BlocoA", andar="1",
                 status="Disponivel", tipo_sala="Sala")
    dados.update(kw)
    return Sala(**dados)


def usuario(**kw):
    dados = dict(id=None, nome="Maria Silva", email="maria@email.com", telefone="69999990000",
                 role="Aluno", senha="Senha123")
    dados.update(kw)
    return Usuario(**dados)


# ---------------- Sala ----------------
def test_nome_da_sala_aceita_ate_10_caracteres():
    sala(nome="a" * Sala.NOME_MAX).validar_nome()


def test_nome_da_sala_com_mais_de_10_caracteres_e_rejeitado():
    with pytest.raises(ValueError, match="no máximo 10"):
        sala(nome="a" * (Sala.NOME_MAX + 1)).validar_nome()


@pytest.mark.parametrize("capacidade", [1, 30, 255, 30.0])
def test_capacidades_validas(capacidade):
    sala(capacidade=capacidade).validar_capacidade()


@pytest.mark.parametrize("capacidade, trecho", [
    (0, "maior que zero"),
    (-5, "maior que zero"),
    ("30", "maior que zero"),
    (256, "no máximo 255"),
    (2.5, "inteiro"),
    (float("inf"), "inteiro"),
])
def test_capacidades_invalidas(capacidade, trecho):
    with pytest.raises(ValueError, match=trecho):
        sala(capacidade=capacidade).validar_capacidade()


@pytest.mark.parametrize("campo, metodo", [("predio", "validar_predio"), ("andar", "validar_andar")])
def test_predio_e_andar_nao_podem_ser_vazios_nem_longos(campo, metodo):
    for vazio in ("", "   ", None):
        with pytest.raises(ValueError, match="Informe"):
            getattr(sala(**{campo: vazio}), metodo)()

    with pytest.raises(ValueError, match="no máximo 15"):
        getattr(sala(**{campo: "x" * 16}), metodo)()

    getattr(sala(**{campo: "x" * 15}), metodo)()


def test_andar_numerico_e_aceito():
    """A coluna é varchar: o número vira texto."""
    sala(andar=2).validar_andar()


# ---------------- Usuario ----------------
def test_nome_e_email_respeitam_o_tamanho_das_colunas():
    usuario(nome="a" * Usuario.NOME_MAX).validar_nome()
    with pytest.raises(ValueError, match="no máximo 100"):
        usuario(nome="a" * (Usuario.NOME_MAX + 1)).validar_nome()

    longo = "a" * (Usuario.EMAIL_MAX - len("@x.com") + 1) + "@x.com"
    with pytest.raises(ValueError, match="no máximo 320"):
        usuario(email=longo).validar_email()


@pytest.mark.parametrize("digitado, esperado", [
    ("69999990000", "69999990000"),
    ("(69) 99999-0000", "69999990000"),
    ("69 9999-0000", "6999990000"),
])
def test_telefone_e_gravado_so_com_digitos(digitado, esperado):
    u = usuario(telefone=digitado)
    u.validar_telefone()
    assert u.telefone_normalizado == esperado
    assert len(u.telefone_normalizado) <= 11  # cabe na coluna varchar(11)


def test_eh_admin():
    assert usuario(role="Admin").eh_admin is True
    assert usuario(role="Professor").eh_admin is False
    assert usuario(role="Aluno").eh_admin is False


def test_coletar_erros_devolve_todos_de_uma_vez():
    erros = usuario(nome="A", email="invalido", telefone="123", role="Chefe").coletar_erros()

    assert len(erros) == 4


def test_coletar_erros_so_confere_a_senha_quando_pedido():
    u = usuario(senha="curta")

    assert u.coletar_erros() == []
    assert len(u.coletar_erros(incluir_senha=True)) == 1


def test_coletar_erros_com_dados_validos():
    assert usuario().coletar_erros(incluir_senha=True) == []
