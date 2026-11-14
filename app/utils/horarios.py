from datetime import time, timedelta

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