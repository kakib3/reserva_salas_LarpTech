import re

class Usuario:
    ROLES_VALIDAS = ["Aluno", "Professor", "Admin"]
    
    def __init__(self, id, nome, email, telefone, role, senha, status="Ativo"):   #adicionado status
        self.id = id; self.nome = nome; self.email = email
        self.telefone = telefone; self.role = role; self.senha = senha
        self.status = status
        
    def validar_nome(self, tamanho_minimo=2):
        if not isinstance(self.nome, str) or len(self.nome.strip()) < tamanho_minimo:
            raise ValueError(f"Nome deve ter pelo {tamanho_minimo} caracteres.")

    def validar_email(self):
        padrao = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not isinstance(self.email, str) or not re.match(padrao, self.email):
            raise ValueError("Email inválido")
        
    def validar_telefone(self):
        digitos = re.sub(r"\D", "", str(self.telefone))
        if len(digitos) < 10 or len(digitos) > 11:
            raise ValueError("Telefone deve conter entre 10 e 11 dígitos (DDD + número).")
        
    def validar_role(self):
        if self.role not in Usuario.ROLES_VALIDAS:
            raise ValueError(f"Role invalida. Deve ser uma das: {', '.join(Usuario.ROLES_VALIDAS)}.")

    def validar_senha(self, tamanho_minimo=4):
        if not isinstance(self.senha, str) or len(self.senha) < tamanho_minimo:
            raise ValueError(f"Senha deve ter pelo menos {tamanho_minimo} caracteres.")