from app.controllers import usuarios_controller
from app.utils import sessao

def entrar(email, senha):
    ok, mensagem, usuario = usuarios_controller.fazer_login(email, senha)

    if ok:
        sessao.login_sessao(usuario)
    
    return ok, mensagem, usuario

def sair():
    sessao.logout_sessao()
    return True, "Sessão encerrada.", None

def usuario_atual():
    return sessao.usuario_logado()