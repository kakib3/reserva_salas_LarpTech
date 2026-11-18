import re

from app.models.constantes import PapelUsuario


class Usuario:
    # Limites das colunas da tabela `usuarios`
    NOME_MAX = 100
    EMAIL_MAX = 320

    ROLES_VALIDAS = [PapelUsuario.ALUNO, PapelUsuario.PROFESSOR, PapelUsuario.ADMIN]
    
    def __init__(self, id, nome, email, telefone, role, senha, status="Ativo"):   #adicionado status
        self.id = id; self.nome = nome; self.email = email
        self.telefone = telefone; self.role = role; self.senha = senha
        self.status = status
        
    def validar_nome(self, tamanho_minimo=2):
        if not isinstance(self.nome, str) or len(self.nome.strip()) < tamanho_minimo:
            raise ValueError(f"Nome deve ter pelo menos {tamanho_minimo} caracteres.")
        if len(self.nome) > Usuario.NOME_MAX:
            raise ValueError(f"Nome deve ter no máximo {Usuario.NOME_MAX} caracteres.")

    def validar_email(self):
        padrao = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not isinstance(self.email, str) or not re.match(padrao, self.email):
            raise ValueError("Email inválido")
        if len(self.email) > Usuario.EMAIL_MAX:
            raise ValueError(f"Email deve ter no máximo {Usuario.EMAIL_MAX} caracteres.")
        
    @property
    def telefone_normalizado(self):
        """Só os dígitos: é assim que o telefone é gravado (coluna varchar(11))."""
        return re.sub(r"\D", "", str(self.telefone))

    @property
    def eh_admin(self):
        return self.role == PapelUsuario.ADMIN

    def coletar_erros(self, incluir_senha=False):
        """Roda todas as validações e devolve a lista de mensagens (vazia se tudo certo)."""
        validacoes = [
            self.validar_nome,
            self.validar_email,
            self.validar_telefone,
            self.validar_role,
        ]
        if incluir_senha:
            validacoes.append(self.validar_senha)

        erros = []
        for validar in validacoes:
            try:
                validar()
            except ValueError as e:
                erros.append(str(e))
        return erros

    def validar_telefone(self):
        digitos = self.telefone_normalizado
        if len(digitos) < 10 or len(digitos) > 11:
            raise ValueError("Telefone deve conter entre 10 e 11 dígitos (DDD + número).")
        
    def validar_role(self):
        if self.role not in Usuario.ROLES_VALIDAS:
            raise ValueError(f"Role invalida. Deve ser uma das: {', '.join(Usuario.ROLES_VALIDAS)}.")

    def validar_senha(self, tamanho_minimo=8, tamanho_maximo_bytes=72):
        if not isinstance(self.senha, str) or len(self.senha) < tamanho_minimo:
            raise ValueError(f"Senha deve ter pelo menos {tamanho_minimo} caracteres.")
        if not re.search(r"[A-Za-z]", self.senha) or not re.search(r"\d", self.senha):
            raise ValueError("A senha deve conter pelo menos uma letra e um número.")
        # O bcrypt só aceita até 72 bytes; acima disso a geração do hash falha.
        if len(self.senha.encode("utf-8")) > tamanho_maximo_bytes:
            raise ValueError(f"Senha deve ter no máximo {tamanho_maximo_bytes} bytes.")