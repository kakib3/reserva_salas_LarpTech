from app.models.constantes import StatusSala, TipoSala


class Sala:
    # Limites das colunas da tabela `salas`
    NOME_MAX = 10
    CAPACIDADE_MAX = 255
    PREDIO_MAX = 15
    ANDAR_MAX = 15

    STATUS_VALIDOS = [
        StatusSala.DISPONIVEL,
        StatusSala.MANUTENCAO,
        StatusSala.INDISPONIVEL
    ]

    TIPOS_VALIDOS = [
        TipoSala.SALA,
        TipoSala.REUNIAO,
        TipoSala.LABORATORIO,
        TipoSala.AUDITORIO
    ]

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
        if len(self.nome) > Sala.NOME_MAX:
            raise ValueError(f"Nome da sala deve ter no máximo {Sala.NOME_MAX} caracteres.")

    def validar_capacidade(self):
        if not isinstance(self.capacidade, (int, float)) or self.capacidade <= 0:
            raise ValueError("Capacidade deve ser um número maior que zero.")
        if not float(self.capacidade).is_integer():
            raise ValueError("Capacidade deve ser um número inteiro.")
        if self.capacidade > Sala.CAPACIDADE_MAX:
            raise ValueError(f"Capacidade deve ser no máximo {Sala.CAPACIDADE_MAX}.")

    def validar_predio(self):
        self._validar_texto_curto(self.predio, "prédio", Sala.PREDIO_MAX)

    def validar_andar(self):
        self._validar_texto_curto(self.andar, "andar", Sala.ANDAR_MAX)

    def validar_status(self):
        if self.status not in Sala.STATUS_VALIDOS:
            raise ValueError(f"Status inválido. Deve ser um dos: {', '.join(Sala.STATUS_VALIDOS)}.")

    def validar_tipo_sala(self):
        if self.tipo_sala not in Sala.TIPOS_VALIDOS:
            raise ValueError(f"Tipo de sala inválido. Deve ser um dos: {', '.join(Sala.TIPOS_VALIDOS)}.")

    @staticmethod
    def _validar_texto_curto(valor, rotulo, maximo):
        texto = "" if valor is None else str(valor)  # a coluna é varchar: aceita número (ex.: andar 2)
        if not texto.strip():
            raise ValueError(f"Informe o {rotulo} da sala.")
        if len(texto) > maximo:
            raise ValueError(f"O {rotulo} da sala deve ter no máximo {maximo} caracteres.")
