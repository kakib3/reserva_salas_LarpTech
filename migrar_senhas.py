"""Migração ÚNICA das senhas em texto puro para hash bcrypt.

Como usar (na raiz do projeto, com o .streamlit/secrets.toml configurado):

    1. Faça BACKUP do banco.
    2. Rode:  python migrar_senhas.py
    3. Confirme digitando SIM.

Quem já tem hash bcrypt é ignorado, então rodar duas vezes é seguro.
Tudo é gravado numa única transação: se algo falhar, nada é alterado.

Faça a migração no mesmo momento em que publicar a versão com hash. Com o código
novo e senhas ainda em texto puro, ninguém consegue entrar; com o código antigo e
senhas já em hash, também não.
"""
import re

from app.models.conexao import conectar_banco
from app.utils.seguranca import gerar_hash_senha

# Formato do hash bcrypt: $2a$/$2b$/$2y$ + custo (2 dígitos) + 53 caracteres.
_PADRAO_HASH_BCRYPT = re.compile(r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$")


def _ja_eh_hash(senha):
    return isinstance(senha, str) and _PADRAO_HASH_BCRYPT.match(senha) is not None


def migrar():
    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT id_usuario, email, senha FROM usuarios")
        usuarios = cursor.fetchall()

        migrados = 0
        ignorados = 0
        com_erro = []

        for usuario in usuarios:
            if _ja_eh_hash(usuario["senha"]):
                ignorados += 1
                continue

            try:
                novo_hash = gerar_hash_senha(usuario["senha"])
            except ValueError as erro:
                # Ex.: senha vazia ou com mais de 72 bytes (limite do bcrypt).
                com_erro.append((usuario["email"], str(erro)))
                continue

            cursor.execute(
                "UPDATE usuarios SET senha = %s WHERE id_usuario = %s",
                (novo_hash, usuario["id_usuario"])
            )
            migrados += 1

        if com_erro:
            conexao.rollback()
            print("Nada foi alterado. Corrija estes usuários e rode de novo:")
            for email, motivo in com_erro:
                print(f"  - {email}: {motivo}")
            return

        conexao.commit()
        print(f"Migração concluída: {migrados} migrados, {ignorados} já estavam com hash.")

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


if __name__ == "__main__":
    resposta = input("Já fez o backup do banco? Digite SIM para migrar as senhas: ")

    if resposta.strip() == "SIM":
        migrar()
    else:
        print("Cancelado. Nenhuma senha foi alterada.")
