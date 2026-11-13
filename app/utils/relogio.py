from datetime import datetime
from zoneinfo import ZoneInfo

FUSO = ZoneInfo("America/Porto_Velho")

def agora():
    return datetime.now(FUSO)

def hoje():
    return agora().date()