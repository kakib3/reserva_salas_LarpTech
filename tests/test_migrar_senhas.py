import migrar_senhas
from app.utils.seguranca import gerar_hash_senha, verificar_senha


class _Cursor:
    def __init__(self, banco):
        self.banco = banco

    def execute(self, sql, params=()):
        sql = " ".join(sql.split())

        if sql.startswith("SELECT id_usuario, email, senha FROM usuarios"):
            self._linhas = [dict(u) for u in self.banco.usuarios.values()]
        elif sql.startswith("UPDATE usuarios SET senha"):
            senha, id_usuario = params
            self.banco.pendentes[id_usuario] = senha
        else:
            raise AssertionError(f"SQL não previsto no teste: {sql}")

    def fetchall(self):
        return self._linhas

    def close(self):
        pass


class _Conexao:
    def __init__(self, banco):
        self.banco = banco

    def cursor(self, dictionary=False):
        return _Cursor(self.banco)

    def commit(self):
        self.banco.usuarios_atualizar()
        self.banco.commits += 1

    def rollback(self):
        self.banco.pendentes.clear()
        self.banco.rollbacks += 1

    def close(self):
        pass


class _Banco:
    def __init__(self, usuarios):
        self.usuarios = {u["id_usuario"]: u for u in usuarios}
        self.pendentes = {}
        self.commits = 0
        self.rollbacks = 0

    def usuarios_atualizar(self):
        for id_usuario, senha in self.pendentes.items():
            self.usuarios[id_usuario]["senha"] = senha
        self.pendentes.clear()


def _usar_banco(monkeypatch, usuarios):
    banco = _Banco(usuarios)
    monkeypatch.setattr(migrar_senhas, "conectar_banco", lambda: _Conexao(banco))
    return banco


def test_migra_senha_em_texto_puro_para_hash(monkeypatch):
    banco = _usar_banco(monkeypatch, [
        {"id_usuario": 1, "email": "a@x.com", "senha": "Senha@123"},
    ])

    migrar_senhas.migrar()

    assert banco.usuarios[1]["senha"] != "Senha@123"
    assert verificar_senha("Senha@123", banco.usuarios[1]["senha"]) is True
    assert banco.commits == 1


def test_nao_refaz_hash_de_quem_ja_migrou(monkeypatch):
    ja_hash = gerar_hash_senha("Senha@123")
    banco = _usar_banco(monkeypatch, [
        {"id_usuario": 1, "email": "a@x.com", "senha": ja_hash},
    ])

    migrar_senhas.migrar()

    assert banco.usuarios[1]["senha"] == ja_hash


def test_se_um_usuario_falhar_nada_e_alterado(monkeypatch):
    banco = _usar_banco(monkeypatch, [
        {"id_usuario": 1, "email": "a@x.com", "senha": "Senha@123"},
        {"id_usuario": 2, "email": "b@x.com", "senha": ""},
    ])

    migrar_senhas.migrar()

    assert banco.usuarios[1]["senha"] == "Senha@123"
    assert banco.commits == 0
    assert banco.rollbacks == 1
