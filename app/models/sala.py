class Sala:
    STATUS_VALIDOS = ["Disponivel", "Manutencao", "Indisponivel"]
    TIPOS_VALIDOS = ["SALA", "REUNIAO", "LABORATORIO", "AUDITORIO"]

    def __init__(self, id, nome, capacidade, predio, andar, status, tipo_sala):
        self.id = id
        self.nome = nome
        self.capacidade = capacidade
        self.predio = predio
        self.andar = andar
        self.status = status
        self.tipo_sala = tipo_sala

    def validar_nome(self, tamanho_minimo=2):
        if not isinstance(self.nome, str) or len(self.nome.strip()) < tamanho_minimo:
            raise ValueError(f"Nome da sala deve ter pelo menos {tamanho_minimo} caracteres.")

    def validar_capacidade(self):
        if not isinstance(self.capacidade, (int, float)) or self.capacidade <= 0:
            raise ValueError("Capacidade deve ser um número maior que zero.")

    def validar_status(self):
        if self.status not in Sala.STATUS_VALIDOS:
            raise ValueError(f"Status inválido. Deve ser um dos: {', '.join(Sala.STATUS_VALIDOS)}.")

    def validar_tipo_sala(self):
        if self.tipo_sala not in Sala.TIPOS_VALIDOS:
            raise ValueError(f"Tipo de sala inválido. Deve ser um dos: {', '.join(Sala.TIPOS_VALIDOS)}.")