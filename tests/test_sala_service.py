import shutil
import unittest

from app.models.dados import DATA_DIR, carregar_salas, carregar_usuarios
from app.services import sala_service
from app.utils import salas_ocultas

ID_SALA = 1


class TestSalaService(unittest.TestCase):

    def setUp(self):
        for nome in ("usuarios.csv", "salas.csv"):
            origem = DATA_DIR / nome
            backup = DATA_DIR / f"{origem.stem}_backup.csv"
            shutil.copy(origem, backup)
            self.addCleanup(self._restaurar, origem, backup)

        salas_ocultas.mostrar_sala(ID_SALA)
        self.addCleanup(salas_ocultas.mostrar_sala, ID_SALA)

        usuarios = carregar_usuarios()
        self.id_admin = int(usuarios[usuarios["role"] == "Admin"].iloc[0]["idUser"])
        self.id_comum = int(usuarios[usuarios["role"] != "Admin"].iloc[0]["idUser"])

    @staticmethod
    def _restaurar(origem, backup):
        shutil.copy(backup, origem)
        backup.unlink()

    def _desativar_admin(self):
        usuarios = carregar_usuarios()
        usuarios.loc[usuarios["idUser"] == self.id_admin, "status"] = "Inativo"
        usuarios.to_csv(DATA_DIR / "usuarios.csv", sep=";", index=False)

    def _sala(self, id_sala=ID_SALA):
        salas = carregar_salas()
        return salas[salas["idSala"] == id_sala].iloc[0]

    # --- cadastrar / alterar / mudar status: deve ser negado -------------

    def test_usuario_comum_nao_cadastra_sala(self):
        total = len(carregar_salas())

        with self.assertRaises(PermissionError):
            sala_service.criar_sala("Sala99", 20, "Anexo1", 1, "Disponivel", "SALA", self.id_comum)

        self.assertEqual(len(carregar_salas()), total)

    def test_solicitante_invalido_nao_cadastra_sala(self):
        for solicitante in (None, 99999):
            with self.subTest(solicitante=solicitante):
                with self.assertRaises(PermissionError):
                    sala_service.criar_sala("Sala99", 20, "Anexo1", 1, "Disponivel", "SALA", solicitante)

    def test_admin_inativo_nao_cadastra_sala(self):
        self._desativar_admin()

        with self.assertRaises(PermissionError):
            sala_service.criar_sala("Sala99", 20, "Anexo1", 1, "Disponivel", "SALA", self.id_admin)

    def test_usuario_comum_nao_altera_sala(self):
        capacidade = self._sala()["capacidade"]

        with self.assertRaises(PermissionError):
            sala_service.alterar_sala(ID_SALA, "Sala01", 999, "Anexo1", 1, "SALA", self.id_comum)

        self.assertEqual(self._sala()["capacidade"], capacidade)

    def test_usuario_comum_nao_muda_status_da_sala(self):
        status = self._sala()["status"]

        with self.assertRaises(PermissionError):
            sala_service.alterar_status_sala(ID_SALA, "Manutencao", self.id_comum)

        self.assertEqual(self._sala()["status"], status)

    # --- cadastrar / alterar / mudar status: deve funcionar --------------

    def test_admin_cadastra_sala(self):
        total = len(carregar_salas())

        sala = sala_service.criar_sala("Sala99", 20, "Anexo1", 1, "Disponivel", "SALA", self.id_admin)

        self.assertEqual(len(carregar_salas()), total + 1)
        self.assertEqual(sala.nome, "Sala99")

    def test_admin_altera_sala(self):
        resultado = sala_service.alterar_sala(ID_SALA, "Sala01", 31, "Anexo1", 1, "SALA", self.id_admin)

        self.assertIsNot(False, resultado)
        self.assertEqual(self._sala()["capacidade"], 31)

    def test_admin_muda_status_da_sala(self):
        resultado = sala_service.alterar_status_sala(ID_SALA, "Manutencao", self.id_admin)

        self.assertTrue(resultado)
        self.assertEqual(self._sala()["status"], "Manutencao")

    def test_admin_com_status_invalido_recebe_erro_de_validacao(self):
        with self.assertRaises(ValueError):
            sala_service.alterar_status_sala(ID_SALA, "Quebrada", self.id_admin)

    def test_admin_muda_status_de_sala_inexistente(self):
        self.assertFalse(sala_service.alterar_status_sala(999, "Manutencao", self.id_admin))

    # --- ocultar / mostrar ------------------------------------------------

    def test_usuario_comum_nao_oculta_sala(self):
        with self.assertRaises(PermissionError):
            sala_service.ocultar_sala(ID_SALA, self.id_comum)

        self.assertFalse(salas_ocultas.esta_oculta(ID_SALA))

    def test_solicitante_invalido_nao_oculta_sala(self):
        for solicitante in (None, 99999):
            with self.subTest(solicitante=solicitante):
                with self.assertRaises(PermissionError):
                    sala_service.ocultar_sala(ID_SALA, solicitante)

        self.assertFalse(salas_ocultas.esta_oculta(ID_SALA))

    def test_admin_inativo_nao_oculta_sala(self):
        self._desativar_admin()

        with self.assertRaises(PermissionError):
            sala_service.ocultar_sala(ID_SALA, self.id_admin)

        self.assertFalse(salas_ocultas.esta_oculta(ID_SALA))

    def test_usuario_comum_nao_mostra_sala_oculta(self):
        sala_service.ocultar_sala(ID_SALA, self.id_admin)

        with self.assertRaises(PermissionError):
            sala_service.mostrar_sala(ID_SALA, self.id_comum)

        self.assertTrue(salas_ocultas.esta_oculta(ID_SALA))

    def test_listar_ocultas_nao_expoe_o_conjunto_interno(self):
        with self.assertRaises(AttributeError):
            salas_ocultas.listar_ocultas().add(ID_SALA)

        self.assertFalse(salas_ocultas.esta_oculta(ID_SALA))

    def test_admin_oculta_e_mostra_sala(self):
        sala_service.ocultar_sala(ID_SALA, self.id_admin)
        self.assertTrue(salas_ocultas.esta_oculta(ID_SALA))

        sala_service.mostrar_sala(ID_SALA, self.id_admin)
        self.assertFalse(salas_ocultas.esta_oculta(ID_SALA))


if __name__ == "__main__":
    unittest.main()