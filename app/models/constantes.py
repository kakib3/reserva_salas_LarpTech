class StatusReserva:
    CONFIRMADA = "Confirmada"
    PENDENTE = "Pendente"
    CANCELADA = "Cancelada"
    
    ATIVAS = (CONFIRMADA, PENDENTE)
    
class PapelUsuario:
    ALUNO = "Aluno"
    PROFESSOR = "Professor"
    ADMIN = "Admin"

class StatusUsuario:
    ATIVO = "Ativo"
    INATIVO = "Inativo"


class StatusSala:
    DISPONIVEL = "Disponivel"
    MANUTENCAO = "Manutencao"
    INDISPONIVEL = "Indisponivel"
    
class TipoSala:
    SALA = "Sala"
    REUNIAO = "Reuniao"
    LABORATORIO = "Laboratorio"
    AUDITORIO = "Auditorio"
    
    PRECISA_APROVACAO = (LABORATORIO, AUDITORIO)
    