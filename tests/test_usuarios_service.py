import shutil
import unittest

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


if __name__ == "__main__":
    unittest.main()