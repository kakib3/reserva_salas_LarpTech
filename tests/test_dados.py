
import pandas as pd
import pytest

from app.models.dados import _ler_csv, _salvar_csv
from app.utils.excecoes import ErroDeDados


# ---------------------------------------------------------------------------
# Leitura de CSV
# ---------------------------------------------------------------------------

def test_ler_csv_arquivo_inexistente(tmp_path):
    arquivo = tmp_path / "usuarios.csv"

    with pytest.raises(ErroDeDados, match="não foi encontrado"):
        _ler_csv(arquivo)


def test_ler_csv_arquivo_vazio(tmp_path):
    arquivo = tmp_path / "usuarios.csv"
    arquivo.write_text("", encoding="utf-8")

    with pytest.raises(ErroDeDados, match="está vazio"):
        _ler_csv(arquivo)


def test_ler_csv_arquivo_malformado(tmp_path):
    arquivo = tmp_path / "usuarios.csv"
    arquivo.write_text(
        "idUser;nome;email;telefone;role;senha;status\n"
        "1;Joao;joao@email.com;999;Aluno;123;Ativo\n"
        "2;Maria;email;999;Aluno;123;Ativo;campo_extra\n",
        encoding="utf-8"
    )

    with pytest.raises(ErroDeDados, match="está malformado"):
        _ler_csv(arquivo)


def test_ler_csv_com_colunas_ausentes(tmp_path):
    arquivo = tmp_path / "usuarios.csv"
    arquivo.write_text(
        "idUser;nome;email\n"
        "1;Joao;joao@email.com\n",
        encoding="utf-8"
    )

    with pytest.raises(ErroDeDados, match="está incompleto"):
        _ler_csv(arquivo)


def test_ler_csv_tipo_de_arquivo_nao_reconhecido(tmp_path):
    arquivo = tmp_path / "outro.csv"
    arquivo.write_text(
        "id;nome\n1;Joao\n",
        encoding="utf-8"
    )

    with pytest.raises(ErroDeDados, match="não reconhecido"):
        _ler_csv(arquivo)


def test_ler_csv_valido(tmp_path):
    arquivo = tmp_path / "salas.csv"

    df_original = pd.DataFrame({
        "idSala": [1],
        "nome": ["Sala 01"],
        "capacidade": [30],
        "predio": ["Bloco A"],
        "andar": ["1"],
        "status": ["Disponível"],
        "tipoSala": ["Comum"]
    })

    df_original.to_csv(arquivo, sep=";", index=False)

    resultado = _ler_csv(arquivo)

    df_original["andar"] = pd.to_numeric(df_original["andar"])

    pd.testing.assert_frame_equal(
        resultado,
        df_original,
        check_dtype=False
)
    


def test_ler_csv_preserva_senha_e_telefone_como_texto(tmp_path):
    arquivo = tmp_path / "usuarios.csv"

    arquivo.write_text(
        "idUser;nome;email;telefone;role;senha;status\n"
        "1;Joao;joao@email.com;06999999999;Aluno;001234;Ativo\n",
        encoding="utf-8"
    )

    resultado = _ler_csv(
        arquivo,
        dtype={"senha": str, "telefone": str}
    )

    assert resultado.iloc[0]["senha"] == "001234"
    assert resultado.iloc[0]["telefone"] == "06999999999"

    assert isinstance(resultado.iloc[0]["senha"], str)
    assert isinstance(resultado.iloc[0]["telefone"], str)


def test_ler_csv_sem_permissao(tmp_path, monkeypatch):
    arquivo = tmp_path / "usuarios.csv"

    def falhar_leitura(*args, **kwargs):
        raise PermissionError("Acesso negado")

    monkeypatch.setattr(pd, "read_csv", falhar_leitura)

    with pytest.raises(ErroDeDados, match="Sem permissão"):
        _ler_csv(arquivo)


def test_salvar_csv_grava_corretamente(tmp_path):
    arquivo = tmp_path / "usuarios.csv"

    df = pd.DataFrame({
        "idUser": [1, 2],
        "nome": ["Joao", "Maria"]
    })

    _salvar_csv(df, arquivo)

    resultado = pd.read_csv(arquivo, sep=";")

    pd.testing.assert_frame_equal(resultado, df)


def test_salvar_csv_cria_diretorio_inexistente(tmp_path):
    arquivo = tmp_path / "nova_pasta" / "usuarios.csv"

    df = pd.DataFrame({
        "idUser": [1],
        "nome": ["Joao"]
    })

    _salvar_csv(df, arquivo)

    assert arquivo.exists()


def test_salvar_csv_sem_permissao(tmp_path, monkeypatch):
    arquivo = tmp_path / "usuarios.csv"

    df = pd.DataFrame({
        "idUser": [1],
        "nome": ["Joao"]
    })

    def falhar_gravacao(*args, **kwargs):
        raise PermissionError("Acesso negado")

    monkeypatch.setattr(pd.DataFrame, "to_csv", falhar_gravacao)

    with pytest.raises(ErroDeDados, match="Sem permissão"):
        _salvar_csv(df, arquivo)


def test_salvar_csv_falha_no_replace_preserva_original(
    tmp_path,
    monkeypatch
):
    arquivo = tmp_path / "usuarios.csv"

    arquivo.write_text(
        "idUser;nome\n1;Original\n",
        encoding="utf-8"
    )

    conteudo_original = arquivo.read_text(encoding="utf-8")

    df = pd.DataFrame({
        "idUser": [2],
        "nome": ["Novo"]
    })

    def falhar_replace(*args, **kwargs):
        raise OSError("Falha simulada")

    monkeypatch.setattr("app.models.dados.os.replace", falhar_replace)

    with pytest.raises(ErroDeDados, match="Não foi possível gravar"):
        _salvar_csv(df, arquivo)

    assert arquivo.read_text(encoding="utf-8") == conteudo_original


def test_salvar_csv_remove_temporario_apos_falha(
    tmp_path,
    monkeypatch
):
    arquivo = tmp_path / "usuarios.csv"

    df = pd.DataFrame({
        "idUser": [1],
        "nome": ["Joao"]
    })

    def falhar_replace(*args, **kwargs):
        raise OSError("Falha simulada")

    monkeypatch.setattr("app.models.dados.os.replace", falhar_replace)

    with pytest.raises(ErroDeDados):
        _salvar_csv(df, arquivo)

    temporarios = list(tmp_path.glob(".usuarios_*.tmp"))

    assert temporarios == []