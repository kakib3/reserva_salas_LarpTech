

class Reserva:
    def __init__(self, id, usuario_id, sala_id, data, hora_inicio, hora_fim, status, criado_em):
        self.id = id
        self.usuario_id = usuario_id
        self.sala_id = sala_id
        self.data = data
        self.hora_inicio = hora_inicio
        self.hora_fim = hora_fim
        self.status = status
        self.criado_em = criado_em