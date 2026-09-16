from datetime import time, date

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
        
    def validar_horario(self):
        if not isinstance(self.hora_inicio, time) or not isinstance(self.hora_fim, time):
            raise ValueError("Hora de início e hora de fim devem ser objetos do tipo 'time'.")
        if self.hora_inicio >= self.hora_fim:
            raise ValueError("Hora de início deve ser anterior à hora de fim.")
        
    def validar_intervalo(self, intervalo_minimo=30, intervalo_maximo=240):
        duracao = (self.hora_fim.hour * 60 + self.hora_fim.minute) - (self.hora_inicio.hour * 60 + self.hora_inicio.minute)
        if duracao < intervalo_minimo:
            raise ValueError(f"A duração da reserva deve ser de pelo menos {intervalo_minimo} minutos.")
        if duracao > intervalo_maximo:
            raise ValueError(f"A duração da reserva não pode exceder {intervalo_maximo} minutos.")
        
    def validar_horario_funcionamento(self):
        hora_abertura = time(7, 0)
        hora_fechamento = time(22, 0)

        if self.hora_inicio < hora_abertura or self.hora_inicio > hora_fechamento or self.hora_fim < hora_abertura or self.hora_fim > hora_fechamento:
            raise ValueError(f"As reservas devem respeitar o horário de funcionamento da instituição: das {hora_abertura.strftime('%H:%M')} às {hora_fechamento.strftime('%H:%M')}.")
        
    def validar_dia_util(self):
        if self.data.weekday() > 5:  #invalida apenas a reserva de domingo, pois há sábados letivos
            raise ValueError("As reservas só podem ser feitas em dias úteis e em sábados letivos.")