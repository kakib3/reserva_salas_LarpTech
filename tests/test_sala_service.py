
import unittest
from datetime import timedelta
from unittest.mock import MagicMock, patch

from app.services import sala_service
from app.models.constantes import StatusSala, StatusReserva


ID_SALA = 1
ID_ADMIN = 10
ID_COMUM = 20


class TestSalaService(unittest.TestCase):

    def setUp(self):
        self.conexao = MagicMock()
        self.cursor = MagicMock()

        self.conexao.cursor.return_value = self.cursor

        patcher = patch.object(
            sala_service,
            "conectar_banco",
            return_value=self.conexao
        )
        self.mock_conectar = patcher.start()
        self.addCleanup(patcher.stop)

    def _sala(self, **alteracoes):
        sala = {
            "id_sala": ID_SALA,
            "nome": "Sala 01",
            "capacidade": 30,
            "predio": "Bloco A",
            "andar": 1,
            "status_sala": StatusSala.DISPONIVEL,
            "tipo_sala": "Sala"
        }

        sala.update(alteracoes)
        return sala

    # --- listar e buscar salas -------------------------------------------

    def test_listar_salas_retorna_resultados(self):
        salas = [self._sala(), self._sala(id_sala=2)]
        self.cursor.fetchall.return_value = salas

        resultado = sala_service.listar_salas()

        self.assertEqual(resultado, salas)
        self.cursor.execute.assert_called_once_with(
            "SELECT * FROM salas"
        )
        self.cursor.close.assert_called_once()
        self.conexao.close.assert_called_once()

    def test_listar_salas_retorna_lista_vazia(self):
        self.cursor.fetchall.return_value = []

        resultado = sala_service.listar_salas()

        self.assertEqual(resultado, [])

    def test_buscar_sala_por_id_retorna_sala(self):
        sala = self._sala()
        self.cursor.fetchone.return_value = sala

        resultado = sala_service.buscar_sala_por_id(ID_SALA)

        self.assertEqual(resultado, sala)
        self.cursor.execute.assert_called_once_with(
            "SELECT * FROM salas WHERE id_sala = %s",
            (ID_SALA,)
        )

    def test_buscar_sala_inexistente_retorna_none(self):
        self.cursor.fetchone.return_value = None

        resultado = sala_service.buscar_sala_por_id(999)

        self.assertIsNone(resultado)

    # --- criar sala ------------------------------------------------------

    @patch.object(sala_service.usuarios_service, "exigir_admin")
    def test_admin_cadastra_sala(self, mock_exigir_admin):
        resultado = sala_service.criar_sala(
            "Sala 02",
            20,
            "Bloco B",
            2,
            StatusSala.DISPONIVEL,
            "Sala",
            ID_ADMIN
        )

        self.assertTrue(resultado)
        mock_exigir_admin.assert_called_once_with(ID_ADMIN)
        self.cursor.execute.assert_called_once()
        self.conexao.commit.assert_called_once()
        self.cursor.close.assert_called_once()
        self.conexao.close.assert_called_once()

    @patch.object(sala_service.usuarios_service, "exigir_admin")
    def test_criar_sala_com_nome_invalido(self, mock_exigir_admin):
        with self.assertRaises(ValueError):
            sala_service.criar_sala(
                "A",
                20,
                "Bloco B",
                2,
                StatusSala.DISPONIVEL,
                "Sala",
                ID_ADMIN
            )

        self.mock_conectar.assert_not_called()

    @patch.object(sala_service.usuarios_service, "exigir_admin")
    def test_criar_sala_com_capacidade_invalida(self, mock_exigir_admin):
        with self.assertRaises(ValueError):
            sala_service.criar_sala(
                "Sala 02",
                0,
                "Bloco B",
                2,
                StatusSala.DISPONIVEL,
                "Sala",
                ID_ADMIN
            )

        self.mock_conectar.assert_not_called()

    @patch.object(sala_service.usuarios_service, "exigir_admin")
    def test_criar_sala_com_status_invalido(self, mock_exigir_admin):
        with self.assertRaises(ValueError):
            sala_service.criar_sala(
                "Sala 02",
                20,
                "Bloco B",
                2,
                "Quebrada",
                "Sala",
                ID_ADMIN
            )

        self.mock_conectar.assert_not_called()

    @patch.object(sala_service.usuarios_service, "exigir_admin")
    def test_criar_sala_com_tipo_invalido(self, mock_exigir_admin):
        with self.assertRaises(ValueError):
            sala_service.criar_sala(
                "Sala 02",
                20,
                "Bloco B",
                2,
                StatusSala.DISPONIVEL,
                "Tipo inválido",
                ID_ADMIN
            )

        self.mock_conectar.assert_not_called()

    @patch.object(sala_service.usuarios_service, "exigir_admin")
    def test_criar_sala_exige_administrador(self, mock_exigir_admin):
        mock_exigir_admin.side_effect = PermissionError

        with self.assertRaises(PermissionError):
            sala_service.criar_sala(
                "Sala 02",
                20,
                "Bloco B",
                2,
                StatusSala.DISPONIVEL,
                "Sala",
                ID_COMUM
            )

        self.mock_conectar.assert_not_called()

    # --- alterar sala ----------------------------------------------------

    @patch.object(sala_service.usuarios_service, "exigir_admin")
    def test_admin_altera_sala(self, mock_exigir_admin):
        self.cursor.fetchone.return_value = {
            "id_sala": ID_SALA,
            "status_sala": StatusSala.DISPONIVEL
        }

        resultado = sala_service.alterar_sala(
            ID_SALA,
            "Sala 03",
            40,
            "Bloco B",
            2,
            "Sala",
            ID_ADMIN
        )

        self.assertTrue(resultado)
        self.assertEqual(self.cursor.execute.call_count, 2)
        self.conexao.commit.assert_called_once()

    @patch.object(sala_service.usuarios_service, "exigir_admin")
    def test_alterar_sala_inexistente_retorna_false(self, mock_exigir_admin):
        self.cursor.fetchone.return_value = None

        resultado = sala_service.alterar_sala(
            999,
            "Sala 03",
            40,
            "Bloco B",
            2,
            "Sala",
            ID_ADMIN
        )

        self.assertFalse(resultado)
        self.assertEqual(self.cursor.execute.call_count, 1)
        self.conexao.commit.assert_not_called()

    @patch.object(sala_service.usuarios_service, "exigir_admin")
    def test_alterar_sala_com_capacidade_invalida(self, mock_exigir_admin):
        self.cursor.fetchone.return_value = {
            "id_sala": ID_SALA,
            "status_sala": StatusSala.DISPONIVEL
        }

        with self.assertRaises(ValueError):
            sala_service.alterar_sala(
                ID_SALA,
                "Sala 03",
                -1,
                "Bloco B",
                2,
                "Sala",
                ID_ADMIN
            )

        self.conexao.commit.assert_not_called()

    # --- alterar status --------------------------------------------------

    @patch.object(sala_service.usuarios_service, "exigir_admin")
    def test_admin_altera_status_da_sala(self, mock_exigir_admin):
        self.cursor.fetchone.return_value = {
            "status_sala": StatusSala.DISPONIVEL
        }

        resultado = sala_service.alterar_status_sala(
            ID_SALA,
            StatusSala.MANUTENCAO,
            ID_ADMIN
        )

        self.assertTrue(resultado)
        self.assertEqual(self.cursor.execute.call_count, 2)
        self.conexao.commit.assert_called_once()

    @patch.object(sala_service.usuarios_service, "exigir_admin")
    def test_alterar_status_de_sala_inexistente(self, mock_exigir_admin):
        self.cursor.fetchone.return_value = None

        resultado = sala_service.alterar_status_sala(
            999,
            StatusSala.MANUTENCAO,
            ID_ADMIN
        )

        self.assertFalse(resultado)
        self.conexao.commit.assert_not_called()

    @patch.object(sala_service.usuarios_service, "exigir_admin")
    def test_alterar_para_o_mesmo_status_retorna_false(self, mock_exigir_admin):
        self.cursor.fetchone.return_value = {
            "status_sala": StatusSala.DISPONIVEL
        }

        resultado = sala_service.alterar_status_sala(
            ID_SALA,
            StatusSala.DISPONIVEL,
            ID_ADMIN
        )

        self.assertFalse(resultado)
        self.assertEqual(self.cursor.execute.call_count, 1)
        self.conexao.commit.assert_not_called()

    @patch.object(sala_service.usuarios_service, "exigir_admin")
    def test_alterar_status_invalido_gera_erro(self, mock_exigir_admin):
        with self.assertRaises(ValueError):
            sala_service.alterar_status_sala(
                ID_SALA,
                "Quebrada",
                ID_ADMIN
            )

        self.mock_conectar.assert_not_called()

    # --- consultar salas -------------------------------------------------

    @patch.object(sala_service.usuarios_service, "checar_admin")
    @patch.object(sala_service.salas_ocultas, "esta_oculta")
    @patch.object(sala_service, "listar_salas")
    def test_consultar_salas_retorna_todas_para_admin(
        self,
        mock_listar,
        mock_oculta,
        mock_admin
    ):
        mock_admin.return_value = True
        mock_oculta.return_value = False
        mock_listar.return_value = [
            self._sala(),
            self._sala(id_sala=2, nome="Sala 02")
        ]

        resultado = sala_service.consultar_salas(ID_ADMIN)

        self.assertEqual(len(resultado), 2)
        self.assertTrue(resultado[0]["pode_gerenciar"])

    @patch.object(sala_service.usuarios_service, "checar_admin")
    @patch.object(sala_service.salas_ocultas, "esta_oculta")
    @patch.object(sala_service, "listar_salas")
    def test_usuario_comum_nao_visualiza_sala_oculta(
        self,
        mock_listar,
        mock_oculta,
        mock_admin
    ):
        mock_admin.return_value = False
        mock_oculta.side_effect = lambda id_sala: id_sala == ID_SALA
        mock_listar.return_value = [
            self._sala(),
            self._sala(id_sala=2, nome="Sala 02")
        ]

        resultado = sala_service.consultar_salas(ID_COMUM)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["id_sala"], 2)

    @patch.object(sala_service.usuarios_service, "checar_admin")
    @patch.object(sala_service.salas_ocultas, "esta_oculta")
    @patch.object(sala_service, "listar_salas")
    def test_consultar_somente_salas_disponiveis(
        self,
        mock_listar,
        mock_oculta,
        mock_admin
    ):
        mock_admin.return_value = True
        mock_oculta.return_value = False
        mock_listar.return_value = [
            self._sala(),
            self._sala(
                id_sala=2,
                status_sala=StatusSala.MANUTENCAO
            )
        ]

        resultado = sala_service.consultar_salas(
            ID_ADMIN,
            somente_disponiveis=True
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(
            resultado[0]["status_sala"],
            StatusSala.DISPONIVEL
        )

    @patch.object(sala_service.usuarios_service, "checar_admin")
    @patch.object(sala_service.salas_ocultas, "esta_oculta")
    @patch.object(sala_service, "listar_salas")
    def test_consultar_salas_por_capacidade_minima(
        self,
        mock_listar,
        mock_oculta,
        mock_admin
    ):
        mock_admin.return_value = True
        mock_oculta.return_value = False
        mock_listar.return_value = [
            self._sala(capacidade=20),
            self._sala(id_sala=2, capacidade=40)
        ]

        resultado = sala_service.consultar_salas(
            ID_ADMIN,
            capacidade_minima=30
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["capacidade"], 40)

    @patch.object(sala_service.usuarios_service, "checar_admin")
    @patch.object(sala_service.salas_ocultas, "esta_oculta")
    @patch.object(sala_service, "listar_salas")
    def test_consultar_salas_por_predio(
        self,
        mock_listar,
        mock_oculta,
        mock_admin
    ):
        mock_admin.return_value = True
        mock_oculta.return_value = False
        mock_listar.return_value = [
            self._sala(predio="Bloco A"),
            self._sala(id_sala=2, predio="Bloco B")
        ]

        resultado = sala_service.consultar_salas(
            ID_ADMIN,
            predio="Bloco B"
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["predio"], "Bloco B")

    @patch.object(sala_service.usuarios_service, "checar_admin")
    @patch.object(sala_service.salas_ocultas, "esta_oculta")
    @patch.object(sala_service, "listar_salas")
    def test_consultar_predios_retorna_lista_ordenada(
        self,
        mock_listar,
        mock_oculta,
        mock_admin
    ):
        mock_admin.return_value = True
        mock_oculta.return_value = False
        mock_listar.return_value = [
            self._sala(predio="Bloco C"),
            self._sala(id_sala=2, predio="Bloco A"),
            self._sala(id_sala=3, predio="Bloco B")
        ]

        resultado = sala_service.consultar_predios(ID_ADMIN)

        self.assertEqual(
            resultado,
            ["Bloco A", "Bloco B", "Bloco C"]
        )

    # --- salas para reserva e salas disponíveis -------------------------

    @patch.object(sala_service.usuarios_service, "checar_usuario_ativo")
    @patch.object(sala_service, "consultar_salas")
    def test_consultar_salas_para_reserva(
        self,
        mock_consultar,
        mock_usuario_ativo
    ):
        mock_usuario_ativo.return_value = True

        mock_consultar.return_value = [
            self._sala(oculta=False),
            self._sala(id_sala=2, nome="Sala 02", oculta=True)
        ]

        resultado = sala_service.consultar_salas_para_reserva(ID_COMUM)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["id_sala"], ID_SALA)
        self.assertFalse(resultado[0]["oculta"])

        mock_consultar.assert_called_once_with(
            ID_COMUM,
            somente_disponiveis=True
        )

    @patch.object(sala_service.usuarios_service, "checar_usuario_ativo")
    def test_usuario_inativo_nao_consulta_salas_para_reserva(
        self,
        mock_usuario_ativo
    ):
        mock_usuario_ativo.return_value = False

        with self.assertRaises(PermissionError):
            sala_service.consultar_salas_para_reserva(ID_COMUM)

    @patch.object(sala_service.salas_ocultas, "esta_oculta")
    @patch.object(sala_service, "listar_salas")
    def test_consultar_salas_disponiveis(
        self,
        mock_listar,
        mock_oculta
    ):
        mock_oculta.side_effect = lambda id_sala: id_sala == 2
        mock_listar.return_value = [
            self._sala(),
            self._sala(id_sala=2),
            self._sala(
                id_sala=3,
                status_sala=StatusSala.MANUTENCAO
            )
        ]

        resultado = sala_service.consultar_salas_disponiveis()

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["id_sala"], ID_SALA)

    @patch.object(sala_service.salas_ocultas, "esta_oculta")
    @patch.object(sala_service, "listar_salas")
    def test_consultar_salas_disponiveis_respeita_limite(
        self,
        mock_listar,
        mock_oculta
    ):
        mock_oculta.return_value = False
        mock_listar.return_value = [
            self._sala(id_sala=1),
            self._sala(id_sala=2),
            self._sala(id_sala=3)
        ]

        resultado = sala_service.consultar_salas_disponiveis(limite=2)

        self.assertEqual(len(resultado), 2)

    # --- consultar disponibilidade -------------------------------------

    @patch.object(sala_service.salas_ocultas, "esta_oculta")
    @patch.object(sala_service, "buscar_sala_por_id")
    def test_consultar_disponibilidade_de_sala_inexistente(
        self,
        mock_buscar,
        mock_oculta
    ):
        mock_buscar.return_value = None

        resultado = sala_service.consultar_disponibilidade(
            999,
            "2026-11-14"
        )

        self.assertIsNone(resultado)
        self.mock_conectar.assert_not_called()

    @patch.object(sala_service.salas_ocultas, "esta_oculta")
    @patch.object(sala_service.usuarios_service, "checar_admin")
    @patch.object(sala_service, "buscar_sala_por_id")
    def test_usuario_comum_nao_consulta_disponibilidade_de_sala_oculta(
        self,
        mock_buscar,
        mock_admin,
        mock_oculta
    ):
        mock_buscar.return_value = self._sala()
        mock_oculta.return_value = True
        mock_admin.return_value = False

        resultado = sala_service.consultar_disponibilidade(
            ID_SALA,
            "2026-11-14",
            ID_COMUM
        )

        self.assertIsNone(resultado)
        self.mock_conectar.assert_not_called()

    @patch.object(sala_service.salas_ocultas, "esta_oculta")
    @patch.object(sala_service, "buscar_sala_por_id")
    def test_consultar_disponibilidade_sem_reservas(
        self,
        mock_buscar,
        mock_oculta
    ):
        mock_buscar.return_value = self._sala()
        mock_oculta.return_value = False
        self.cursor.fetchall.return_value = []

        resultado = sala_service.consultar_disponibilidade(
            ID_SALA,
            "2026-11-14"
        )

        self.assertTrue(resultado["reservavel"])
        self.assertEqual(resultado["reservas"], [])
        self.assertEqual(
            resultado["horarios_livres"],
            [
                (
                    __import__("datetime").time(7, 0),
                    __import__("datetime").time(22, 0)
                )
            ]
        )

    @patch.object(sala_service.salas_ocultas, "esta_oculta")
    @patch.object(sala_service, "buscar_sala_por_id")
    def test_consultar_disponibilidade_calcula_intervalos(
        self,
        mock_buscar,
        mock_oculta
    ):
        from datetime import time

        mock_buscar.return_value = self._sala()
        mock_oculta.return_value = False

        self.cursor.fetchall.return_value = [
            {
                "id_reserva": 1,
                "id_usuario": 20,
                "nome_usuario": "Usuário",
                "data_reserva": "2026-11-14",
                "hora_inicio": timedelta(hours=9),
                "hora_fim": timedelta(hours=10),
                "status_reserva": StatusReserva.CONFIRMADA
            },
            {
                "id_reserva": 2,
                "id_usuario": 21,
                "nome_usuario": "Outro usuário",
                "data_reserva": "2026-11-14",
                "hora_inicio": timedelta(hours=13),
                "hora_fim": timedelta(hours=14),
                "status_reserva": StatusReserva.PENDENTE
            }
        ]

        resultado = sala_service.consultar_disponibilidade(
            ID_SALA,
            "2026-11-14"
        )

        self.assertEqual(
            resultado["horarios_livres"],
            [
                (time(7, 0), time(9, 0)),
                (time(10, 0), time(13, 0)),
                (time(14, 0), time(22, 0))
            ]
        )

        self.assertIsInstance(
            resultado["reservas"][0]["hora_inicio"],
            time
        )

    @patch.object(sala_service.salas_ocultas, "esta_oculta")
    @patch.object(sala_service, "buscar_sala_por_id")
    def test_sala_indisponivel_nao_possui_horarios_livres(
        self,
        mock_buscar,
        mock_oculta
    ):
        mock_buscar.return_value = self._sala(
            status_sala=StatusSala.MANUTENCAO
        )
        mock_oculta.return_value = False
        self.cursor.fetchall.return_value = []

        resultado = sala_service.consultar_disponibilidade(
            ID_SALA,
            "2026-11-14"
        )

        self.assertFalse(resultado["reservavel"])
        self.assertEqual(resultado["horarios_livres"], [])

    # --- ocultar e mostrar salas -----------------------------------------

    @patch.object(sala_service.usuarios_service, "exigir_admin")
    @patch.object(sala_service.salas_ocultas, "ocultar_sala")
    def test_admin_oculta_sala(
        self,
        mock_ocultar,
        mock_exigir_admin
    ):
        sala_service.ocultar_sala(ID_SALA, ID_ADMIN)

        mock_exigir_admin.assert_called_once_with(ID_ADMIN)
        mock_ocultar.assert_called_once_with(ID_SALA)

    @patch.object(sala_service.usuarios_service, "exigir_admin")
    @patch.object(sala_service.salas_ocultas, "mostrar_sala")
    def test_admin_mostra_sala(
        self,
        mock_mostrar,
        mock_exigir_admin
    ):
        sala_service.mostrar_sala(ID_SALA, ID_ADMIN)

        mock_exigir_admin.assert_called_once_with(ID_ADMIN)
        mock_mostrar.assert_called_once_with(ID_SALA)

    @patch.object(sala_service.usuarios_service, "exigir_admin")
    @patch.object(sala_service.salas_ocultas, "ocultar_sala")
    def test_usuario_comum_nao_oculta_sala(
        self,
        mock_ocultar,
        mock_exigir_admin
    ):
        mock_exigir_admin.side_effect = PermissionError

        with self.assertRaises(PermissionError):
            sala_service.ocultar_sala(ID_SALA, ID_COMUM)

        mock_ocultar.assert_not_called()

    @patch.object(sala_service.usuarios_service, "exigir_admin")
    @patch.object(sala_service.salas_ocultas, "mostrar_sala")
    def test_usuario_comum_nao_mostra_sala(
        self,
        mock_mostrar,
        mock_exigir_admin
    ):
        mock_exigir_admin.side_effect = PermissionError

        with self.assertRaises(PermissionError):
            sala_service.mostrar_sala(ID_SALA, ID_COMUM)

        mock_mostrar.assert_not_called()


if __name__ == "__main__":
    unittest.main()
