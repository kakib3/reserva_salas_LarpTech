from app.models.conexao import conectar_banco

def carregar_usuarios():
    conexao = conectar_banco()
    cursor = None
    
    try:
        cursor = conexao.cursor(dictionary=True)
        
        cursor.execute("""SELECT id_usuario,
                       nome,
                       email,
                       telefone,
                       papel,
                       status_usuario
                       FROM usuarios""")
        
        return cursor.fetchall()
    
    finally:
        if cursor is not None:
            cursor.close()
            conexao.close()

def carregar_salas():
    
    conexao = conectar_banco()
    cursor = None
    
    try:
        cursor = conexao.cursor(dictionary=True)
            
        cursor.execute("SELECT * FROM salas;")
            
        return cursor.fetchall()
        
    finally:
        if cursor is not None:
            cursor.close()
            conexao.close()


def carregar_reservas():
    
    conexao = conectar_banco()
    cursor = None
    
    try:
        cursor = conexao.cursor(dictionary=True)
            
        cursor.execute("SELECT * FROM reservas;")
            
        return cursor.fetchall()
        
    finally:
        if cursor is not None:
            cursor.close()
            conexao.close()

def obter_reservas_da_sala(id_sala, data=None):
    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        if data is not None:
            sql = "SELECT * FROM reservas WHERE id_sala = %s AND data_reserva = %s;"
            valores = (id_sala, data)

        else:
            sql = "SELECT * FROM reservas WHERE id_sala = %s;"
            valores = (id_sala)

        cursor.execute(sql, valores)
        return cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()
            conexao.close()