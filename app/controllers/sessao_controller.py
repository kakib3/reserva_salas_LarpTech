# Mantém os nomes antigos disponíveis, encaminhando para o controller de usuários.
# A lógica de cadastro, login e manutenção de usuários fica centralizada em um único lugar.
from app.controllers.usuarios_controller import (
    cadastrar_usuario,
    fazer_login,
    editar_usuario,
    trocar_senha,
    desativar_usuario,
    obter_usuario,
    listar_todos_usuarios,
)
