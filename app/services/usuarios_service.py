import pandas as pd

from app.models.dados import DATA_DIR
from app.models.usuario import Usuario


def listar_usuarios():
    arquivo = DATA_DIR / "usuarios.csv"
    return pd.read_csv(arquivo, sep=";", dtype={"senha": str, "telefone": str})


def buscar_usuario_por_id(id_usuario):
    arquivo = DATA_DIR / "usuarios.csv"

    usuarios = pd.read_csv(arquivo, sep=";", dtype={"senha": str, "telefone": str})
    usuario = usuarios[usuarios["idUser"] == id_usuario]

    if usuario.empty:
        return None

    usuario = usuario.iloc[0]

    return Usuario(usuario["idUser"], usuario["nome"], usuario["email"], usuario["telefone"], usuario["role"], usuario["senha"], usuario["status"])  # <-- + usuario["status"]

def buscar_usuario_por_email(email):
    arquivo = DATA_DIR / "usuarios.csv"

    usuarios = pd.read_csv(arquivo, sep=";", dtype={"senha": str, "telefone": str})
    usuario = usuarios[usuarios["email"] == email]

    if usuario.empty:
        return None

    usuario = usuario.iloc[0]

    return Usuario(usuario["idUser"], usuario["nome"], usuario["email"], usuario["telefone"], usuario["role"], usuario["senha"], usuario["status"])  # <-- + usuario["status"]


def verificar_email_disponivel(email, id_usuario_ignorar=None):
    arquivo = DATA_DIR / "usuarios.csv"
    usuarios = pd.read_csv(arquivo, sep=";", dtype={"senha": str, "telefone": str})

    mesmo_email = usuarios["email"] == email

    if id_usuario_ignorar is not None:
        mesmo_email &= usuarios["idUser"] != id_usuario_ignorar

    return usuarios[mesmo_email].empty


def criar_usuario(nome, email, telefone, role, senha):
    arquivo = DATA_DIR / "usuarios.csv"

    usuario_obj = Usuario(None, nome, email, telefone, role, senha)

    usuario_obj.validar_nome()
    usuario_obj.validar_email()
    usuario_obj.validar_telefone()
    usuario_obj.validar_role()
    usuario_obj.validar_senha()

    if not verificar_email_disponivel(email):
        return False

    usuarios = pd.read_csv(arquivo, sep=";", dtype={"senha": str, "telefone": str})
    novo_id = 1 if usuarios.empty else int(usuarios["idUser"].max()) + 1

    novo_usuario = pd.DataFrame([{"idUser": novo_id, "nome": nome, "email": email, "telefone": telefone, "role": role, "senha": senha, "status": "Ativo"}])  # <-- + "status": "Ativo"

    usuarios = pd.concat([usuarios, novo_usuario], ignore_index=True)
    usuarios.to_csv(arquivo, sep=";", index=False)

    return Usuario(novo_id, nome, email, telefone, role, senha, "Ativo")


def autenticar_usuario(email, senha):
    usuario = buscar_usuario_por_email(email)

    if usuario is None:
        return False  

    if usuario.senha != senha:
        return False
    
    if usuario.status == "Inativo":       #verifica se é usuario inativo
        return False    

    return usuario

def alterar_usuario(id_usuario, nome, email, telefone, role):
    arquivo = DATA_DIR / "usuarios.csv"
    usuarios = pd.read_csv(arquivo, sep=";", dtype={"senha": str, "telefone": str} )
    
    usuario_atual = usuarios[usuarios["idUser"] == id_usuario]
    
    if usuario_atual.empty:
        return False
    
    usuario_obj = Usuario(id_usuario, nome, email, telefone, role, usuario_atual.iloc[0]["senha"], usuario_atual.iloc[0]["status"])

    usuario_obj.validar_nome()
    usuario_obj.validar_email()
    usuario_obj.validar_telefone()
    usuario_obj.validar_role()
    
    if not verificar_email_disponivel(email, id_usuario_ignorar=id_usuario):
        return False 
    
    filtro = usuarios["idUser"] == id_usuario
    usuarios.loc[filtro, ["nome", "email", "telefone", "role"]] = [nome, email, telefone, role]

    usuarios.to_csv(arquivo, sep=";", index=False)
    return usuario_obj

def alterar_senha(id_usuario, senha_atual, nova_senha):
    arquivo = DATA_DIR / "usuarios.csv"
    usuarios = pd.read_csv(arquivo, sep=";", dtype={"senha": str, "telefone": str})
    
    usuario_atual =  usuarios[usuarios["idUser"] == id_usuario]
    
    if usuario_atual.empty:
        return False
    
    if usuario_atual.iloc[0]["senha"] != senha_atual:
        return False
    
    usuario_obj = Usuario(id_usuario, usuario_atual.iloc[0]["nome"], usuario_atual.iloc[0]["email"], usuario_atual.iloc[0]["telefone"], usuario_atual.iloc[0]["role"], nova_senha, usuario_atual.iloc[0]["status"])
    usuario_obj.validar_senha()

    usuarios.loc[usuarios["idUser"] == id_usuario, "senha"] = nova_senha
    usuarios.to_csv(arquivo, sep=";", index=False)
    return True

def desativar_usuario(id_usuario):
    arquivo = DATA_DIR / "usuarios.csv"
    usuarios = pd.read_csv(arquivo, sep=";", dtype={"senha": str, "telefone": str})
    
    filtro = usuarios["idUser"] == id_usuario
    
    if not filtro.any():
        return False
    
    if usuarios.loc[filtro, "status"] == "Inativo":
        return False
    
    usuarios.loc[filtro, "status"] = "Inativo"
    usuarios.to_csv(arquivo, sep=";", index=False)
    return True
    