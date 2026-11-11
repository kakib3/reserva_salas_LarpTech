from app.models.conexao import conectar_banco
from app.models.usuario import Usuario


def listar_usuarios(id_solicitante):
    exigir_admin(id_solicitante)

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""SELECT id_usuario, nome, email, telefone,
                       papel, status_usuario FROM usuarios""")

        return cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


def buscar_usuario_por_id(id_usuario):
    conexao = conectar_banco()
    cursor = None
    
    try:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        resultado = cursor.fetchone()
        
        if not resultado:
            return None

        return Usuario(
            resultado["id_usuario"],
            resultado["nome"],
            resultado["email"],
            resultado["telefone"],
            resultado["papel"],
            resultado["senha"],
            resultado["status_usuario"]
        )
        
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

def buscar_usuario_por_email(email):
    conexao = conectar_banco()
    cursor = None
        
    try:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        resultado = cursor.fetchone()
            
        if not resultado:
            return None

        return Usuario(
            resultado["id_usuario"],
            resultado["nome"],
            resultado["email"],
            resultado["telefone"],
            resultado["papel"],
            resultado["senha"],
            resultado["status_usuario"]
        )

    
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

def verificar_email_disponivel(email, id_usuario_ignorar=None):

    conexao = conectar_banco()
    cursor = None
        
    try:
        cursor = conexao.cursor(dictionary=True)
        
        if id_usuario_ignorar is not None:
            cursor.execute(
                """SELECT id_usuario FROM usuarios
                   WHERE email = %s AND id_usuario != %s""",
                (email, id_usuario_ignorar)
            )
        else:
            cursor.execute("SELECT id_usuario FROM usuarios WHERE email = %s", (email,))
            
            return cursor.fetchone() is None
        
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

def criar_usuario(nome, email, telefone, role, senha, id_solicitante=None):
    
    if role == "Admin":
        exigir_admin(id_solicitante)
    conexao = conectar_banco()
    cursor = None
            
    try:
        usuario_obj = Usuario(None, nome, email, telefone, role, senha)
        
        usuario_obj.validar_nome()
        usuario_obj.validar_email()
        usuario_obj.validar_telefone()
        usuario_obj.validar_role()
        usuario_obj.validar_senha()
        
        if not verificar_email_disponivel(email):
                return False
        
        valores = (
            usuario_obj.nome,
            usuario_obj.email,
            usuario_obj.telefone,
            usuario_obj.role,
            usuario_obj.senha,
            usuario_obj.status
        )
        
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("""INSERT INTO usuarios (nome, email, telefone, papel, senha, status_usuario)
                        VALUES
                        (%s, %s, %s, %s, %s, %s)""", valores)
        conexao.commit()
        return True
        
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


def autenticar_usuario(email, senha):
    usuario = buscar_usuario_por_email(email)

    if usuario is None:
        return False  

    if usuario.senha != senha:
        return False
    
    if usuario.status == "Inativo":       #verifica se é usuario inativo
        return False    

    return usuario

def alterar_usuario(id_solicitante, id_usuario, nome, email, telefone, role):
    eh_admin = checar_admin(id_solicitante)
    
    if id_solicitante != id_usuario and not eh_admin:
        raise PermissionError("Você só pode editar os seus próprios dados.")

    conexao = conectar_banco()
    cursor = None
        
    try:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        usuario_atual = cursor.fetchone()
        
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()
            
    if not usuario_atual:
        return False

    role_atual = usuario_atual["papel"]
    
    if role != role_atual:
        if not eh_admin:
            raise PermissionError("Apenas administradores podem alterar o perfil.")
        if role_atual == "Admin" and eh_ultimo_admin(id_usuario):
            raise ValueError("Não é possível rebaixar o último administrador.")
            
    usuario_obj = Usuario(
        id_usuario,
        nome,
        email,
        telefone,
        role,
        usuario_atual["senha"],
        usuario_atual["status_usuario"]
    )
        
    usuario_obj.validar_nome()
    usuario_obj.validar_email()
    usuario_obj.validar_telefone()
    usuario_obj.validar_role()
            
    if not verificar_email_disponivel(email, id_usuario_ignorar=id_usuario):
        return False  
           
    valores = (nome, email, telefone, role, id_usuario)
           
    try:
        cursor = conexao.cursor()
        
        cursor.execute("""UPDATE usuarios
                       SET nome = %s,
                       email = %s,
                       telefone = %s,
                       papel = %s
                       WHERE id_usuario = %s""", valores)
        cursor.commit()
        return usuario_obj
    
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()
    
def alterar_senha(id_solicitante, id_usuario, senha_atual, nova_senha):
    if id_solicitante != id_usuario:
        raise PermissionError("Você só pode alterar a sua própria senha.")

    conexao = conectar_banco()
    cursor = None
    
    try:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        usuario_atual = cursor.fetchone()
    
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()
        
    if not usuario_atual:
        return False

    if usuario_atual["senha"] != senha_atual:
        return False
        
    usuario_obj = Usuario(
        id_usuario,
        usuario_atual["nome"],
        usuario_atual["email"],
        usuario_atual["telefone"],
        usuario_atual["papel"],
        nova_senha,
        usuario_atual["status_usuario"]
    )
        
    usuario_obj.validar_senha()
        
    try:
        cursor = conexao.cursor()
        cursor.execute("UPDATE usuarios SET senha = %s WHERE id_usuario = %s", (nova_senha, id_usuario))
        cursor.commit()
        return True
    
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()
        

def desativar_usuario(id_solicitante, id_usuario):
    exigir_admin(id_solicitante)

    if id_solicitante == id_usuario:
        raise ValueError("Administradores não podem desativar a si mesmos.")

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            "SELECT status_usuario FROM usuarios WHERE id_usuario = %s",
            (id_usuario,)
        )
        resultado = cursor.fetchone()

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

    if not resultado:
        return False

    if resultado["status_usuario"] == "Inativo":
        return False

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor()

        cursor.execute(
            "UPDATE usuarios SET status_usuario = %s WHERE id_usuario = %s",
            ("Inativo", id_usuario)
        )

        conexao.commit()
        return True

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()
 

def checar_admin(id_usuario):
    usuario = buscar_usuario_por_id(id_usuario)
    return (usuario is not None and usuario.role == "Admin" and usuario.status != "Inativo")

def exigir_admin(id_solicitante):
    if id_solicitante is None or not checar_admin(id_solicitante):
        raise PermissionError("Ação não permitida. Apenas administradores podem realizar esta operação.")
    
def eh_ultimo_admin(id_usuario):
    conexao = conectar_banco()
    cursor = None
    
    try:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT id_usuario FROM usuarios WHERE papel = 'Admin' AND status_usuario = 'Ativo'")
        admins = cursor.fetchall()
        return len(admins) == 1 and admins[0]["id_usuario"] == id_usuario
    
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

def obter_usuario(id_solicitante, id_usuario):
    if id_solicitante != id_usuario and not checar_admin(id_solicitante):
        raise PermissionError("Você não tem permissão para ver este usuário.")

    return buscar_usuario_por_id(id_usuario)


def checar_usuario_ativo(id_usuario):
    usuario = buscar_usuario_por_id(id_usuario)
    return usuario is not None and usuario.status != "Inativo"