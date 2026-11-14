import bcrypt


def gerar_hash_senha(senha: str) -> str:
    """Recebe a senha em texto e devolve o hash (com salt embutido) como string."""
    if not isinstance(senha, str) or not senha:
        raise ValueError("Senha inválida para geração de hash.")
    hash_bytes = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())
    return hash_bytes.decode("utf-8")


def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    """Compara a senha digitada com o hash guardado, em tempo constante.

    Retorna False (em vez de lançar) se o hash estiver num formato inesperado —
    por exemplo, uma senha antiga ainda em texto puro.
    """
    if not isinstance(senha, str) or not isinstance(hash_armazenado, str):
        return False
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), hash_armazenado.encode("utf-8"))
    except (ValueError, TypeError):
        return False
