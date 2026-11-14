from datetime import time, timedelta
from app.utils.relogio import agora, hoje

CAMPOS_HORA = ("hora_inicio", "hora_fim")

def normalizar_horarios(registro, campos=CAMPOS_HORA):
    """Converte campos TIME (timedelta) de um registro do MySQL para datetime.time"""
    for campo in campos:
        valor = registro.get(campo)
        
        if isinstance(valor, timedelta):
            segundos = int(valor.total_seconds()) % 86400
            
            registro[campo] = time(
                segundos // 3600,
                (segundos % 3600) // 60,
                segundos % 60
            )
            
def horarios_padrao(data_reserva):
    """Devolve (inicio, fim) sugeridos, ou None se não houver horário hoje."""
    if data_reserva != hoje():
        return time(8,0), time(9,0)
    
    hora = max(agora().hour + 1, 7)
    
    if hora > 21:
        return None
    
    return time(hora, 0), time(hora + 1, 0)