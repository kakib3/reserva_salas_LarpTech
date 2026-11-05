import shutil
import unittest
import pandas as pd  # [NOVO] usado nas comparações de DataFrame

from app.models.dados import DATA_DIR, carregar_usuarios
from app.services import usuarios_service


def _buscar_usuario(admin, ativo=True):
    usuarios = carregar_usuarios()
    filtro = (usuarios["role"] == "Admin") if admin else (usuarios["role"] != "Admin")
    filtro &= (usuarios["status"] != "Inativo") if ativo else (usuarios["status"] == "Inativo")
    achados = usuarios[filtro]
    return achados.iloc[0] if not achados.empty else None


def _campo_usuario(id_usuario, campo):
    usuarios = carregar_usuarios()
    return usuarios[usuarios["idUser"] == id_usuario].iloc[0][campo]


def _definir_status_usuario(id_usuario, status):
    usuarios = carregar_usuarios()
    usuarios.loc[usuarios["idUser"] == id_usuario, "status"] = status
    usuarios.to_csv(DATA_DIR / "usuarios.csv", sep=";", index=False)


# [NOVO] Helpers dos testes complementares
def _definir_role_usuario(id_usuario, role):
    usuarios = carregar_usuarios()
    usuarios.loc[usuarios["idUser"] == id_usuario, "role"] = role
    usuarios.to_csv(DATA_DIR / "usuarios.csv", sep=";", index=False)


def _definir_senha_usuario(id_usuario, senha):
    usuarios = carregar_usuarios()
    usuarios.loc[usuarios["idUser"] == id_usuario, "senha"] = senha
    usuarios.to_csv(DATA_DIR / "usuarios.csv", sep=";", index=False)


def _manter_apenas_este_admin_ativo(id_admin):
    """Desativa todos os outros Admins, para o teste não depender do seed."""
    usuarios = carregar_usuarios()
    outros_admins = (usuarios["role"] == "Admin") & (usuarios["idUser"] != id_admin)
    usuarios.loc[outros_admins, "status"] = "Inativo"
    usuarios.to_csv(DATA_DIR / "usuarios.csv", sep=";", index=False)


class BaseUsuariosTest(unittest.TestCase):
    """Faz backup do usuarios.csv, restaura ao final e separa um Admin e um usuário comum ativos."""

    def setUp(self):
        arquivo = DATA_DIR / "usuarios.csv"
        backup = DATA_DIR / "usuarios_backup.csv"
        shutil.copy(arquivo, backup)
        self.addCleanup(self._restaurar, arquivo, backup)

        self.admin = _buscar_usuario(admin=True)
        self.comum = _buscar_usuario(admin=False)

        if self.admin is None or self.comum is None:
            self.skipTest("É preciso ter um Admin ativo e um usuário comum ativo no usuarios.csv")

        self.id_admin = int(self.admin["idUser"])
        self.id_comum = int(self.comum["idUser"])

    @staticmethod
    def _restaurar(arquivo, backup):
        shutil.copy(backup, arquivo)
        backup.unlink()


EMAIL_TESTE = "teste.auth@example.com"
TELEFONE_TESTE = "11999999999"   # ajuste se o validar_telefone exigir outro formato
SENHA_TESTE = "Senha@123"        # ajuste se o validar_senha exigir outro formato


class TestAutorizacaoUsuarios(BaseUsuariosTest):

    # --- deve ser negado -------------------------------------------------

    def test_usuario_comum_nao_vira_admin(self):
        with self.assertRaises(PermissionError):
            usuarios_service.alterar_usuario(
                self.id_comum, self.id_comum,
                self.comum["nome"], self.comum["email"], self.comum["telefone"], "Admin"
            )

        self.assertEqual(_campo_usuario(self.id_comum, "role"), self.comum["role"])

    def test_usuario_comum_nao_edita_outro_usuario(self):
        with self.assertRaises(PermissionError):
            usuarios_service.alterar_usuario(
                self.id_comum, self.id_admin,
                self.admin["nome"], self.admin["email"], self.admin["telefone"], self.admin["role"]
            )

    def test_usuario_comum_nao_troca_senha_de_outro(self):
        with self.assertRaises(PermissionError):
            usuarios_service.alterar_senha(
                self.id_comum, self.id_admin, self.admin["senha"], SENHA_TESTE
            )

    def test_usuario_comum_nao_desativa_outro(self):
        with self.assertRaises(PermissionError):
            usuarios_service.desativar_usuario(self.id_comum, self.id_admin)

        self.assertNotEqual(_campo_usuario(self.id_admin, "status"), "Inativo")

    def test_admin_nao_desativa_a_si_mesmo(self):
        with self.assertRaises(ValueError):
            usuarios_service.desativar_usuario(self.id_admin, self.id_admin)

        self.assertNotEqual(_campo_usuario(self.id_admin, "status"), "Inativo")

    def test_cadastro_admin_sem_solicitante(self):
        with self.assertRaises(PermissionError):
            usuarios_service.criar_usuario(
                "Teste Auth", EMAIL_TESTE, TELEFONE_TESTE, "Admin", SENHA_TESTE
            )

        self.assertNotIn(EMAIL_TESTE, carregar_usuarios()["email"].values)

    def test_usuario_comum_nao_lista_usuarios(self):
        with self.assertRaises(PermissionError):
            usuarios_service.listar_usuarios(self.id_comum)

    def test_usuario_comum_nao_ve_dados_de_outro(self):
        with self.assertRaises(PermissionError):
            usuarios_service.obter_usuario(self.id_comum, self.id_admin)

    def test_ultimo_admin_nao_pode_ser_rebaixado(self):
        with self.assertRaises(ValueError):
            usuarios_service.alterar_usuario(
                self.id_admin, self.id_admin,
                self.admin["nome"], self.admin["email"], self.admin["telefone"], "Professor"
            )

        self.assertEqual(_campo_usuario(self.id_admin, "role"), "Admin")

    # --- deve funcionar --------------------------------------------------

    def test_auto_cadastro_de_aluno_e_professor(self):
        for role in ("Aluno", "Professor"):
            with self.subTest(role=role):
                resultado = usuarios_service.criar_usuario(
                    "Teste Auth", f"teste.{role.lower()}@example.com", TELEFONE_TESTE,
                    role, SENHA_TESTE
                )

                self.assertIsNot(False, resultado)

    def test_admin_cadastra_outro_admin(self):
        resultado = usuarios_service.criar_usuario(
            "Teste Auth", EMAIL_TESTE, TELEFONE_TESTE,
            "Admin", SENHA_TESTE, self.id_admin
        )

        self.assertIsNot(False, resultado)

    def test_usuario_comum_edita_os_proprios_dados(self):
        resultado = usuarios_service.alterar_usuario(
            self.id_comum, self.id_comum,
            self.comum["nome"], self.comum["email"], self.comum["telefone"], self.comum["role"]
        )

        self.assertIsNot(False, resultado)
        self.assertEqual(_campo_usuario(self.id_comum, "role"), self.comum["role"])

    def test_usuario_comum_troca_a_propria_senha(self):
        resultado = usuarios_service.alterar_senha(
            self.id_comum, self.id_comum, self.comum["senha"], SENHA_TESTE
        )

        self.assertTrue(resultado)

    def test_admin_lista_usuarios_sem_senha(self):
        usuarios = usuarios_service.listar_usuarios(self.id_admin)

        self.assertNotIn("senha", usuarios.columns)

    def test_usuario_comum_ve_os_proprios_dados(self):
        usuario = usuarios_service.obter_usuario(self.id_comum, self.id_comum)

        self.assertIsNotNone(usuario)

    def test_admin_desativa_usuario_comum(self):
        resultado = usuarios_service.desativar_usuario(self.id_admin, self.id_comum)

        self.assertTrue(resultado)
        self.assertEqual(_campo_usuario(self.id_comum, "status"), "Inativo")

    # --- usuário inativo --------------------------------------------------

    def test_usuario_inativo_nao_faz_login(self):
        email, senha = self.comum["email"], self.comum["senha"]
        self.assertIsNot(False, usuarios_service.autenticar_usuario(email, senha))

        _definir_status_usuario(self.id_comum, "Inativo")

        self.assertIs(usuarios_service.autenticar_usuario(email, senha), False)

    def test_checar_usuario_ativo(self):
        self.assertTrue(usuarios_service.checar_usuario_ativo(self.id_comum))
        self.assertFalse(usuarios_service.checar_usuario_ativo(99999))

        _definir_status_usuario(self.id_comum, "Inativo")

        self.assertFalse(usuarios_service.checar_usuario_ativo(self.id_comum))

    def test_admin_inativo_nao_e_admin(self):
        self.assertTrue(usuarios_service.checar_admin(self.id_admin))

        _definir_status_usuario(self.id_admin, "Inativo")

        self.assertFalse(usuarios_service.checar_admin(self.id_admin))


# ---------------------------------------------------------------------------
# [NOVO] Login de usuário
# ---------------------------------------------------------------------------

class TestLoginUsuarios(BaseUsuariosTest):

    def test_login_valido_devolve_o_usuario_certo(self):
        usuario = usuarios_service.autenticar_usuario(self.comum["email"], self.comum["senha"])

        self.assertIsNot(False, usuario)
        self.assertEqual(usuario.email, self.comum["email"])
        self.assertEqual(usuario.role, self.comum["role"])

    def test_login_com_senha_errada_falha(self):
        resultado = usuarios_service.autenticar_usuario(self.comum["email"], "senha-errada")

        self.assertIs(resultado, False)

    def test_login_com_email_inexistente_falha(self):
        resultado = usuarios_service.autenticar_usuario("ninguem@example.com", self.comum["senha"])

        self.assertIs(resultado, False)

    def test_login_com_senha_vazia_ou_none_falha(self):
        for senha in ("", None):
            with self.subTest(senha=senha):
                resultado = usuarios_service.autenticar_usuario(self.comum["email"], senha)

                self.assertIs(resultado, False)

    def test_login_com_a_senha_de_outro_usuario_falha(self):
        senha_do_admin = "Admin@Unica1"
        _definir_senha_usuario(self.id_admin, senha_do_admin)

        resultado = usuarios_service.autenticar_usuario(self.comum["email"], senha_do_admin)

        self.assertIs(resultado, False)

    def test_senha_nova_funciona_e_a_antiga_deixa_de_funcionar(self):
        email, senha_antiga = self.comum["email"], self.comum["senha"]
        self.assertTrue(
            usuarios_service.alterar_senha(self.id_comum, self.id_comum, senha_antiga, SENHA_TESTE)
        )

        self.assertIsNot(False, usuarios_service.autenticar_usuario(email, SENHA_TESTE))
        self.assertIs(usuarios_service.autenticar_usuario(email, senha_antiga), False)


# ---------------------------------------------------------------------------
# [NOVO] E-mail duplicado (verificar_email_disponivel e quem depende dela)
# ---------------------------------------------------------------------------

class TestEmailDisponivel(BaseUsuariosTest):

    def test_email_novo_esta_disponivel(self):
        self.assertTrue(usuarios_service.verificar_email_disponivel("novo.email@example.com"))

    def test_email_ja_cadastrado_nao_esta_disponivel(self):
        self.assertFalse(usuarios_service.verificar_email_disponivel(self.comum["email"]))
        self.assertFalse(usuarios_service.verificar_email_disponivel(self.admin["email"]))

    def test_proprio_email_fica_disponivel_quando_o_proprio_usuario_e_ignorado(self):
        resultado = usuarios_service.verificar_email_disponivel(
            self.comum["email"], id_usuario_ignorar=self.id_comum
        )

        self.assertTrue(resultado)

    def test_email_de_outro_usuario_continua_indisponivel_ao_ignorar_um_id(self):
        resultado = usuarios_service.verificar_email_disponivel(
            self.admin["email"], id_usuario_ignorar=self.id_comum
        )

        self.assertFalse(resultado)

    def test_criar_usuario_com_email_duplicado_nao_grava(self):
        total_antes = len(carregar_usuarios())

        resultado = usuarios_service.criar_usuario(
            "Teste Auth", self.comum["email"], TELEFONE_TESTE, "Aluno", SENHA_TESTE
        )

        self.assertIs(resultado, False)
        self.assertEqual(len(carregar_usuarios()), total_antes)

    def test_alterar_usuario_para_email_de_outro_nao_grava(self):
        resultado = usuarios_service.alterar_usuario(
            self.id_comum, self.id_comum,
            self.comum["nome"], self.admin["email"], self.comum["telefone"], self.comum["role"]
        )

        self.assertIs(resultado, False)
        self.assertEqual(_campo_usuario(self.id_comum, "email"), self.comum["email"])


# ---------------------------------------------------------------------------
# [NOVO] Desativação de usuário
# ---------------------------------------------------------------------------

class TestDesativacaoUsuarios(BaseUsuariosTest):

    def test_desativar_muda_so_o_status_do_alvo(self):
        antes = carregar_usuarios()

        self.assertTrue(usuarios_service.desativar_usuario(self.id_admin, self.id_comum))

        depois = carregar_usuarios()
        alvo = depois["idUser"] == self.id_comum
        self.assertEqual(len(antes), len(depois))
        self.assertEqual(depois.loc[alvo, "status"].iloc[0], "Inativo")
        # nenhuma outra coluna mudou (inclusive a senha do alvo)
        pd.testing.assert_frame_equal(antes.drop(columns="status"), depois.drop(columns="status"))
        # nenhum outro usuário foi afetado
        pd.testing.assert_frame_equal(
            antes[~alvo].reset_index(drop=True), depois[~alvo].reset_index(drop=True)
        )

    def test_desativar_usuario_inexistente_devolve_false_e_nao_altera_o_csv(self):
        antes = carregar_usuarios()

        resultado = usuarios_service.desativar_usuario(self.id_admin, 99999)

        self.assertIs(resultado, False)
        pd.testing.assert_frame_equal(antes, carregar_usuarios())

    def test_desativar_usuario_ja_inativo_devolve_false(self):
        _definir_status_usuario(self.id_comum, "Inativo")

        resultado = usuarios_service.desativar_usuario(self.id_admin, self.id_comum)

        self.assertIs(resultado, False)
        self.assertEqual(_campo_usuario(self.id_comum, "status"), "Inativo")

    def test_solicitante_none_nao_desativa(self):
        with self.assertRaises(PermissionError):
            usuarios_service.desativar_usuario(None, self.id_comum)

        self.assertNotEqual(_campo_usuario(self.id_comum, "status"), "Inativo")

    def test_admin_inativo_nao_desativa(self):
        _definir_status_usuario(self.id_admin, "Inativo")

        with self.assertRaises(PermissionError):
            usuarios_service.desativar_usuario(self.id_admin, self.id_comum)

        self.assertNotEqual(_campo_usuario(self.id_comum, "status"), "Inativo")

    def test_usuario_desativado_nao_loga_e_deixa_de_ser_ativo(self):
        email, senha = self.comum["email"], self.comum["senha"]

        self.assertTrue(usuarios_service.desativar_usuario(self.id_admin, self.id_comum))

        self.assertIs(usuarios_service.autenticar_usuario(email, senha), False)
        self.assertFalse(usuarios_service.checar_usuario_ativo(self.id_comum))


# ---------------------------------------------------------------------------
# [NOVO] Autorização: casos que faltavam
# ---------------------------------------------------------------------------

class TestAutorizacaoUsuariosComplemento(BaseUsuariosTest):

    def test_usuario_comum_nao_cadastra_admin(self):
        with self.assertRaises(PermissionError):
            usuarios_service.criar_usuario(
                "Teste Auth", EMAIL_TESTE, TELEFONE_TESTE, "Admin", SENHA_TESTE, self.id_comum
            )

        self.assertNotIn(EMAIL_TESTE, carregar_usuarios()["email"].values)

    def test_admin_inativo_nao_cadastra_admin(self):
        _definir_status_usuario(self.id_admin, "Inativo")

        with self.assertRaises(PermissionError):
            usuarios_service.criar_usuario(
                "Teste Auth", EMAIL_TESTE, TELEFONE_TESTE, "Admin", SENHA_TESTE, self.id_admin
            )

        self.assertNotIn(EMAIL_TESTE, carregar_usuarios()["email"].values)

    def test_nem_o_admin_troca_a_senha_de_outro_usuario(self):
        with self.assertRaises(PermissionError):
            usuarios_service.alterar_senha(
                self.id_admin, self.id_comum, self.comum["senha"], SENHA_TESTE
            )

        self.assertEqual(_campo_usuario(self.id_comum, "senha"), self.comum["senha"])

    def test_alterar_senha_com_senha_atual_errada_devolve_false_e_nao_muda(self):
        resultado = usuarios_service.alterar_senha(
            self.id_comum, self.id_comum, "senha-atual-errada", SENHA_TESTE
        )

        self.assertIs(resultado, False)
        self.assertEqual(_campo_usuario(self.id_comum, "senha"), self.comum["senha"])

    def test_alterar_usuario_inexistente_devolve_false(self):
        resultado = usuarios_service.alterar_usuario(
            self.id_admin, 99999, "Fulano", "fulano@example.com", TELEFONE_TESTE, "Aluno"
        )

        self.assertIs(resultado, False)

    def test_admin_ve_dados_de_outro_usuario(self):
        usuario = usuarios_service.obter_usuario(self.id_admin, self.id_comum)

        self.assertIsNotNone(usuario)
        self.assertEqual(usuario.email, self.comum["email"])

    def test_obter_usuario_inexistente_devolve_none(self):
        self.assertIsNone(usuarios_service.obter_usuario(self.id_admin, 99999))

    # Versão que não depende do seed (o original só passa se houver um único Admin ativo)
    def test_unico_admin_ativo_nao_pode_ser_rebaixado(self):
        _manter_apenas_este_admin_ativo(self.id_admin)

        with self.assertRaises(ValueError):
            usuarios_service.alterar_usuario(
                self.id_admin, self.id_admin,
                self.admin["nome"], self.admin["email"], self.admin["telefone"], "Professor"
            )

        self.assertEqual(_campo_usuario(self.id_admin, "role"), "Admin")

    def test_com_dois_admins_ativos_um_deles_pode_ser_rebaixado(self):
        _definir_role_usuario(self.id_comum, "Admin")

        resultado = usuarios_service.alterar_usuario(
            self.id_admin, self.id_admin,
            self.admin["nome"], self.admin["email"], self.admin["telefone"], "Professor"
        )

        self.assertIsNot(False, resultado)
        self.assertEqual(_campo_usuario(self.id_admin, "role"), "Professor")


if __name__ == "__main__":
    unittest.main()