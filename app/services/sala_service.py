from app.models.conexao import conectar_banco
from app.models.sala import Sala
from app.services import usuarios_service
from app.utils import salas_ocultas
from app.models.constantes import StatusSala, StatusReserva
from datetime import time, timedelta

def listar_salas():
    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM salas")
        return cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

def buscar_sala_por_id(id_sala):
    
    conexao = conectar_banco()
    cursor = None
    
    try:
        cursor = conexao.cursor(dictionary=True)
            
        cursor.execute("SELECT * FROM salas WHERE id_sala = %s", (id_sala,))
            
        return cursor.fetchone()
        
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
                       ('%s', %s, '%s', '%s', '%s', '%s')""", valores)
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
                    
        cursor.execute("SELECT id_sala FROM salas WHERE id_sala = %s;", (id_sala,))
        resultado = cursor.fetchone()
        if not resultado:
            return False # Sala não encontrada

        sala_obj = Sala(id_sala, nome, capacidade, predio, andar, resultado["status_sala"], tipo_sala)
        sala_obj.validar_nome()
        sala_obj.validar_capacidade()
        sala_obj.validar_tipo_sala()

        valores = (nome, capacidade, predio, andar, tipo_sala, id_sala)
        
        cursor.execute(""" UPDATE salas
                       SET nome = %s,
                       capacidade = %s,
                       predio = %s,
                       andar = %s,
                       tipo_sala = %s
                       WHERE id_sala = %s""", valores)
        conexao.commit()
        return True
    
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


def alterar_status_sala(id_sala, novo_status, id_solicitante):
    usuarios_service.exigir_admin(id_solicitante)

    if novo_status not in Sala.STATUS_VALIDOS:
        raise ValueError(f"Status inválido. Deve ser um dos: {', '.join(Sala.STATUS_VALIDOS)}.")

    conexao = conectar_banco()
    cursor = None
    
    try:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT status_sala FROM salas WHERE id_sala = %s")
        resultado = cursor.fetchone()
        
        if not resultado:
            return False # Sala não encontrada

        if resultado["status_sala"] == novo_status:
            return False # Já está nesse status

        cursor.execute("UPDATE salas SET status_sala = %s WHERE id_sala = %s", (novo_status, id_sala))
        conexao.commit()
        return True
    
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

def consultar_salas(id_usuario, somente_disponiveis=False, capacidade_minima=0, predio=None):
    eh_admin = usuarios_service.checar_admin(id_usuario)
    salas = listar_salas()

    resultado = []

    for sala in salas:
        oculta = salas_ocultas.esta_oculta(sala["id_sala"])

        # Usuários comuns não visualizam salas ocultas
        if oculta and not eh_admin:
            continue

        if somente_disponiveis and sala["status_sala"] != StatusSala.DISPONIVEL:
            continue

        if capacidade_minima and sala["capacidade"] < capacidade_minima:
            continue

        if predio and predio != "Todos" and sala["predio"] != predio:
            continue

        sala["oculta"] = oculta
        sala["pode_gerenciar"] = eh_admin
        resultado.append(sala)

    return resultado


def consultar_predios(id_usuario):
    salas = consultar_salas(id_usuario)

    predios = {
        sala["predio"]
        for sala in salas
        if sala["predio"]
    }

    return sorted(predios)


def consultar_salas_para_reserva(id_usuario):
    if not usuarios_service.checar_usuario_ativo(id_usuario):
        raise PermissionError("É necessário estar logado para consultar salas.")

    salas = consultar_salas(
        id_usuario,
        somente_disponiveis=True
    )

    return [
        sala for sala in salas
        if not sala["oculta"]
    ]


def consultar_salas_disponiveis(limite=5):
    salas = listar_salas()

    disponiveis = [
        sala for sala in salas
        if sala["status_sala"] == StatusSala.DISPONIVEL
        and not salas_ocultas.esta_oculta(sala["id_sala"])
    ]

    return disponiveis[:limite]


def consultar_disponibilidade(id_sala, data_consulta, id_usuario=None):
    sala = buscar_sala_por_id(id_sala)

    if sala is None:
        return None

    # Sala oculta só pode ser consultada por administrador
    if salas_ocultas.esta_oculta(id_sala) and not usuarios_service.checar_admin(id_usuario):
        return None

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """SELECT r.id_reserva,
                      r.id_usuario,
                      u.nome AS nome_usuario,
                      r.data_reserva,
                      r.hora_inicio,
                      r.hora_fim,
                      r.status_reserva
               FROM reservas r
               LEFT JOIN usuarios u
               ON u.id_usuario = r.id_usuario
               WHERE r.id_sala = %s
               AND r.data_reserva = %s
               AND r.status_reserva IN (%s, %s)
               ORDER BY r.hora_inicio""",
            (
                id_sala,
                data_consulta,
                StatusReserva.CONFIRMADA,
                StatusReserva.PENDENTE
            )
        )

        reservas = cursor.fetchall()

        # Normaliza os horários retornados pelo MySQL
        for reserva in reservas:
            for campo in ("hora_inicio", "hora_fim"):
                valor = reserva[campo]

                if isinstance(valor, timedelta):
                    segundos = int(valor.total_seconds()) % 86400

                    reserva[campo] = time(
                        segundos // 3600,
                        (segundos % 3600) // 60,
                        segundos % 60
                    )

    finally:
        if cursor is not None:
            cursor.close()

        conexao.close()

    horarios_livres = []

    if sala["status_sala"] == StatusSala.DISPONIVEL:
        abertura = time(7, 0)
        fechamento = time(22, 0)

        horario_atual = abertura

        for reserva in reservas:
            inicio = reserva["hora_inicio"]
            fim = reserva["hora_fim"]

            duracao = (
                (inicio.hour * 60 + inicio.minute)
                - (horario_atual.hour * 60 + horario_atual.minute)
            )

            if inicio > horario_atual and duracao >= 30:
                horarios_livres.append((horario_atual, inicio))

            if fim > horario_atual:
                horario_atual = fim

        duracao = (
            (fechamento.hour * 60 + fechamento.minute)
            - (horario_atual.hour * 60 + horario_atual.minute)
        )

        if horario_atual < fechamento and duracao >= 30:
            horarios_livres.append((horario_atual, fechamento))

    return {
        "sala": sala,
        "reservavel": sala["status_sala"] == StatusSala.DISPONIVEL,
        "reservas": reservas,
        "horarios_livres": horarios_livres
    }


def ocultar_sala(id_sala, id_solicitante):
    usuarios_service.exigir_admin(id_solicitante)
    salas_ocultas.ocultar_sala(id_sala)


def mostrar_sala(id_sala, id_solicitante):
    usuarios_service.exigir_admin(id_solicitante)
    salas_ocultas.mostrar_sala(id_sala)