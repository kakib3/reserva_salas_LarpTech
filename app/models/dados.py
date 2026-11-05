
import pandas as pd
from pathlib import Path
import os
import tempfile

from app.utils.excecoes import ErroDeDados


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


COLUNAS = {
    "usuarios.csv": [
        "idUser", "nome", "email", "telefone",
        "role", "senha", "status"
    ],
    "salas.csv": [
        "idSala", "nome", "capacidade", "predio",
        "andar", "status", "tipoSala"
    ],
    "reservas.csv": [
        "idReserva", "idUser", "idSala", "data",
        "horaInicio", "horaFim", "status", "criado_em"
    ]
}


def _ler_csv(arquivo, dtype=None):
    try:
        df = pd.read_csv(
            arquivo,
            sep=";",
            dtype=dtype
        )

        nome_arquivo = Path(arquivo).name
        colunas_esperadas = COLUNAS.get(nome_arquivo)

        if colunas_esperadas is None:
            raise ErroDeDados("Tipo de arquivo de dados não reconhecido.")

        faltantes = [
            coluna for coluna in colunas_esperadas
            if coluna not in df.columns
        ]

        if faltantes:
            raise ErroDeDados(
                f"O arquivo {nome_arquivo} está incompleto. "
                f"Colunas ausentes: {', '.join(faltantes)}."
            )

        return df

    except ErroDeDados:
        raise

    except FileNotFoundError:
        raise ErroDeDados(
            f"O arquivo {Path(arquivo).name} não foi encontrado."
        )

    except pd.errors.EmptyDataError:
        raise ErroDeDados(
            f"O arquivo {Path(arquivo).name} está vazio ou sem cabeçalho."
        )

    except pd.errors.ParserError:
        raise ErroDeDados(
            f"O arquivo {Path(arquivo).name} está malformado."
        )

    except UnicodeDecodeError:
        raise ErroDeDados(
            f"Não foi possível interpretar o arquivo {Path(arquivo).name}."
        )

    except PermissionError:
        raise ErroDeDados(
            f"Sem permissão para ler {Path(arquivo).name}."
        )

    except OSError:
        raise ErroDeDados(
            f"Não foi possível acessar {Path(arquivo).name}."
        )


def _salvar_csv(df, arquivo):
    arquivo = Path(arquivo)
    temporario = None

    try:
        arquivo.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            suffix=".tmp",
            prefix=f".{arquivo.stem}_",
            dir=arquivo.parent,
            delete=False
        ) as temp:
            temporario = Path(temp.name)
            df.to_csv(temp, sep=";", index=False)

            temp.flush()
            os.fsync(temp.fileno())

        os.replace(temporario, arquivo)

    except PermissionError:
        raise ErroDeDados(
            f"Sem permissão para gravar {arquivo.name}."
        )

    except OSError:
        raise ErroDeDados(
            f"Não foi possível gravar {arquivo.name}."
        )

    finally:
        if temporario is not None and temporario.exists():
            try:
                temporario.unlink()
            except OSError:
                pass


def carregar_usuarios():
    arquivo = DATA_DIR / "usuarios.csv"

    return _ler_csv(
        arquivo,
        dtype={"senha": str, "telefone": str}
    )


def carregar_salas():
    arquivo = DATA_DIR / "salas.csv"
    return _ler_csv(arquivo)


def carregar_reservas():
    arquivo = DATA_DIR / "reservas.csv"
    return _ler_csv(arquivo)


def obter_reservas_da_sala(id_sala, data=None):
    reservas = carregar_reservas()

    if data is not None:
        return reservas[
            (reservas["idSala"] == id_sala)
            & (reservas["data"] == data)
        ]

    return reservas[reservas["idSala"] == id_sala]
