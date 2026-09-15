import unittest
import shutil

from datetime import date, time

from app.models.dados import DATA_DIR
from app.services.reservas_service import criar_reserva, cancelar_reserva


class TestCriarReserva(unittest.TestCase):

    def setUp(self):
        self.arquivo_reservas = DATA_DIR / "reservas.csv"
        self.backup_reservas = DATA_DIR / "reservas_backup.csv"

        shutil.copy(self.arquivo_reservas, self.backup_reservas)

    def tearDown(self):
        shutil.copy(self.backup_reservas, self.arquivo_reservas)
        self.backup_reservas.unlink()

    def test_criar_reserva_valida(self):
        reserva = criar_reserva(
            1,
            2,
            date(2026, 9, 16),
            time(19, 0),
            time(21, 0)
        )

        self.assertIsNot(False, reserva)

    def test_criar_reserva_com_conflito(self):
        criar_reserva(
            1,
            2,
            date(2026, 9, 16),
            time(19, 0),
            time(21, 0)
        )

        reserva = criar_reserva(
            3,
            2,
            date(2026, 9, 16),
            time(20, 0),
            time(22, 0)
        )

        self.assertIs(reserva, False)

    def test_duracao_menor_que_30_minutos(self):
        with self.assertRaises(ValueError):
            criar_reserva(
                1,
                2,
                date(2026, 9, 16),
                time(19, 0),
                time(19, 20)
            )

    def test_duracao_maior_que_4_horas(self):
        with self.assertRaises(ValueError):
            criar_reserva(
                1,
                2,
                date(2026, 9, 16),
                time(17, 0),
                time(22, 0)
            )

    def test_horario_inicio_igual_ao_fim(self):
        with self.assertRaises(ValueError):
            criar_reserva(
                1,
                2,
                date(2026, 9, 16),
                time(19, 0),
                time(19, 0)
            )

    def test_horario_fora_do_funcionamento(self):
        with self.assertRaises(ValueError):
            criar_reserva(
                1,
                2,
                date(2026, 9, 16),
                time(6, 0),
                time(8, 0)
            )

    def test_reserva_no_domingo(self):
        with self.assertRaises(ValueError):
            criar_reserva(
                1,
                2,
                date(2026, 9, 20),
                time(19, 0),
                time(21, 0)
            )

    def test_sala_em_manutencao(self):
        reserva = criar_reserva(
            1,
            7,
            date(2026, 9, 16),
            time(19, 0),
            time(21, 0)
        )

        self.assertIs(reserva, False)

    def test_sala_indisponivel(self):
        reserva = criar_reserva(
            1,
            10,
            date(2026, 9, 16),
            time(19, 0),
            time(21, 0)
        )

        self.assertIs(reserva, False)

    def test_sala_inexistente(self):
        reserva = criar_reserva(
            1,
            999,
            date(2026, 9, 16),
            time(19, 0),
            time(21, 0)
        )

        self.assertIs(reserva, False)

    def test_sala_comum_fica_confirmada(self):
        reserva = criar_reserva(
            1,
            2,
            date(2026, 9, 16),
            time(19, 0),
            time(21, 0)
        )

        self.assertIsNot(False, reserva)
        self.assertEqual(reserva.status, "Confirmada")

    def test_laboratorio_fica_pendente(self):
        reserva = criar_reserva(
            1,
            6,
            date(2026, 9, 16),
            time(19, 0),
            time(21, 0)
        )

        self.assertIsNot(False, reserva)
        self.assertEqual(reserva.status, "Pendente")

    def test_auditorio_fica_pendente(self):
        reserva = criar_reserva(
            1,
            11,
            date(2026, 9, 16),
            time(19, 0),
            time(21, 0)
        )

        self.assertIsNot(False, reserva)
        self.assertEqual(reserva.status, "Pendente")

class TestCancelarReserva(unittest.TestCase):

    def setUp(self):
        self.arquivo_reservas = DATA_DIR / "reservas.csv"
        self.backup_reservas = DATA_DIR / "reservas_backup.csv"

        shutil.copy(self.arquivo_reservas, self.backup_reservas)

    def tearDown(self):
        shutil.copy(self.backup_reservas, self.arquivo_reservas)
        self.backup_reservas.unlink()

    def test_cancelar_propria_reserva_confirmada(self):
        resultado = cancelar_reserva(1, 4)

        self.assertTrue(resultado)

    def test_cancelar_propria_reserva_pendente(self):
        resultado = cancelar_reserva(8, 7)

        self.assertTrue(resultado)

    def test_cancelar_reserva_de_outro_usuario(self):
        resultado = cancelar_reserva(1, 7)

        self.assertFalse(resultado)

    def test_cancelar_reserva_ja_cancelada(self):
        resultado = cancelar_reserva(5, 4)

        self.assertFalse(resultado)

    def test_cancelar_reserva_inexistente(self):
        resultado = cancelar_reserva(999, 1)

        self.assertFalse(resultado)   
        
if __name__ == "__main__":
    unittest.main()