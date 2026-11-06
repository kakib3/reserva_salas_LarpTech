from app.models.conexao import conectar_banco
from app.models.dados import DATA_DIR, carregar_salas, _salvar_csv
from app.models.sala import Sala
from app.services import usuarios_service
from app.utils import salas_ocultas


def listar_salas():
    return carregar_salas()


def buscar_sala_por_id(id_sala):
    
    conexao = conectar_banco()
    cursor = None
    
    try:
        cursor = conexao.cursor(dictionary=True)
            
        cursor.execute("SELECT * FROM salas WHERE id_sala = %s;", id_sala)
            
        return cursor.fetchall()
        
    finally:
        if cursor is not None:
            cursor.close()
            conexao.close()


def criar_sala(nome, capacidade, predio, andar, status, tipo_sala, id_solicitante):
    usuarios_service.exigir_admin(id_solicitante)  # PermissionError se não for Admin ativo


    sala_obj = Sala(None, nome, capacidade, predio, andar, status, tipo_sala)

    sala_obj.validar_nome()
    sala_obj.validar_capacidade()
    sala_obj.validar_status()
    sala_obj.validar_tipo_sala()
    
    valores = (nome, capacidade, predio, andar, status, tipo_sala)
    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor()
                
        cursor.execute("""INSERT INTO salas (nome, capacidade, predio, andar, status_sala, tipo_sala)
                       VALUES
                       ('%s', %s, '%s', '%s', '%s', '%s');""", valores)
        conexao.commit()
        return True
            
    finally:
        if cursor is not None:
            cursor.close()
            conexao.close()    


def alterar_sala(id_sala, nome, capacidade, predio, andar, tipo_sala, id_solicitante):
    usuarios_service.exigir_admin(id_solicitante)

    conexao = conectar_banco()
    cursor = None
    
    try:
        cursor = conexao.cursor(dictionary=True)
                    
        cursor.execute("SELECT id_sala FROM salas WHERE id_sala = %s;", id_sala)
        resultado = cursor.fetchall()
        if not resultado:
            return False # Sala não encontrada

        sala_obj = Sala(id_sala, nome, capacidade, predio, andar, tipo_sala)
        sala_obj.validar_nome()
        sala_obj.validar_capacidade()
        sala_obj.validar_tipo_sala()

        valores = (nome, capacidade, predio, andar, tipo_sala, id_sala)
        
        cursor.execute(""" UPDATE salas
                       SET nome = '%s',
                       capacidade = %s,
                       predio = '%s',
                       andar = '%s',
                       tipo_sala = '%s'
                       WHERE id_sala = %s;""", valores)
        conexao.commit()
        return True
    
    finally:
        if cursor is not None:
            cursor.close()
            conexao.close()


def alterar_status_sala(id_sala, novo_status, id_solicitante):
    usuarios_service.exigir_admin(id_solicitante)

    arquivo = DATA_DIR / "salas.csv"
    salas = carregar_salas()

    if novo_status not in Sala.STATUS_VALIDOS:
        raise ValueError(f"Status inválido. Deve ser um dos: {', '.join(Sala.STATUS_VALIDOS)}.")

    conexao = conectar_banco()
    cursor = None
    
    try:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT status_sala FROM salas WHERE id_sala = %s;")
        resultado = cursor.fetchall()
        
        if not resultado:
            return False # Sala não encontrada

        if resultado[0]['status_sala'] == novo_status:
            return False # Já está nesse status


        cursor.execute("UPDATE salas SET status_sala = %s WHERE id_sala = %s", novo_status, id_sala)
        conexao.commit()
        return True
    
    finally:
        if cursor is not None:
            cursor.close()
            conexao.close()


def ocultar_sala(id_sala, id_solicitante):
    usuarios_service.exigir_admin(id_solicitante)
    salas_ocultas.ocultar_sala(id_sala)


def mostrar_sala(id_sala, id_solicitante):
    usuarios_service.exigir_admin(id_solicitante)
    salas_ocultas.mostrar_sala(id_sala)