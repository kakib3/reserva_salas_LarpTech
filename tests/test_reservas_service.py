import unittest
import shutil
import pandas as pd

from datetime import date, time, datetime

from app.models.dados import DATA_DIR, carregar_reservas, carregar_usuarios, carregar_salas
from app.services.reservas_service import (
    criar_reserva,
    cancelar_reserva,
    alterar_reserva,
    aprovar_reserva,
    negar_reserva,
)


# ---------------------------------------------------------------------------
# Helpers: leem os IDs direto dos CSVs, então não há IDs "chumbados" nos testes
# de autorização.
# ---------------------------------------------------------------------------

def _buscar_usuario(admin, ativo=True):
    usuarios = carregar_usuarios()
    filtro = (usuarios["role"] == "Admin") if admin else (usuarios["role"] != "Admin")
    filtro &= (usuarios["status"] != "Inativo") if ativo else (usuarios["status"] == "Inativo")
    achados = usuarios[filtro]
    return achados.iloc[0] if not achados.empty else None


def _buscar_reserva(status):
    reservas = carregar_reservas()
    achadas = reservas[reservas["status"] == status]
    return int(achadas.iloc[0]["idReserva"]) if not achadas.empty else None


def _status_reserva(id_reserva):
    reservas = carregar_reservas()
    return reservas[reservas["idReserva"] == id_reserva].iloc[0]["status"]


def _garantir_reserva_pendente():
    """Devolve o ID de uma reserva Pendente. Se não houver nenhuma no CSV,
    transforma uma Confirmada em Pendente (o CSV é restaurado no fim do teste)."""
    reservas = carregar_reservas()
    pendentes = reservas[reservas["status"] == "Pendente"]
    if not pendentes.empty:
        return int(pendentes.iloc[0]["idReserva"])

    confirmadas = reservas[reservas["status"] == "Confirmada"]
    if confirmadas.empty:
        return None

    id_reserva = int(confirmadas.iloc[0]["idReserva"])
    reservas.loc[reservas["idReserva"] == id_reserva, "status"] = "Pendente"
    reservas.to_csv(DATA_DIR / "reservas.csv", sep=";", index=False)
    return id_reserva


def _definir_status_usuario(id_usuario, status):
    usuarios = carregar_usuarios()
    usuarios.loc[usuarios["idUser"] == id_usuario, "status"] = status
    usuarios.to_csv(DATA_DIR / "usuarios.csv", sep=";", index=False)


# ---------------------------------------------------------------------------
# Classes base: backup/restauração dos CSVs
# ---------------------------------------------------------------------------

class BaseCSVTest(unittest.TestCase):
    """Faz backup de reservas.csv e usuarios.csv e restaura ao final."""

    ARQUIVOS = ["reservas.csv", "usuarios.csv"]

    def setUp(self):
        self.arquivo_reservas = DATA_DIR / "reservas.csv"

        for nome in self.ARQUIVOS:
            origem = DATA_DIR / nome
            backup = DATA_DIR / f"{origem.stem}_backup.csv"
            shutil.copy(origem, backup)
            self.addCleanup(self._restaurar, origem, backup)

    @staticmethod
    def _restaurar(origem, backup):
        shutil.copy(backup, origem)
        backup.unlink()


class BaseAutorizacaoTest(BaseCSVTest):
    """Pega um Admin ativo e um usuário comum ativo do usuarios.csv."""

    def setUp(self):
        super().setUp()
        self.admin = _buscar_usuario(admin=True)
        self.comum = _buscar_usuario(admin=False)

        if self.admin is None or self.comum is None:
            self.skipTest("É preciso ter um Admin ativo e um usuário comum ativo no usuarios.csv")

        self.id_admin = int(self.admin["idUser"])
        self.id_comum = int(self.comum["idUser"])


# ---------------------------------------------------------------------------
# Reservas: criar / cancelar / alterar
# ---------------------------------------------------------------------------


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
        
class TestAlterarReserva(unittest.TestCase):

    def setUp(self):
        self.arquivo_reservas = DATA_DIR / "reservas.csv"
        self.backup_reservas = DATA_DIR / "reservas_backup.csv"

        shutil.copy(self.arquivo_reservas, self.backup_reservas)

    def tearDown(self):
        shutil.copy(self.backup_reservas, self.arquivo_reservas)
        self.backup_reservas.unlink()

    def test_alterar_reserva_de_outro_usuario(self):
        resultado = alterar_reserva(
            1,
            7,
            3,
            date(2026, 6, 16),
            time(19, 0),
            time(21, 0)
        )

        self.assertFalse(resultado)

    def test_alterar_reserva_cancelada(self):
        resultado = alterar_reserva(
            5,
            4,
            3,
            date(2026, 6, 16),
            time(19, 0),
            time(21, 0)
        )

        self.assertFalse(resultado)

    def test_alterar_para_sala_indisponivel(self):
        resultado = alterar_reserva(
            1,
            4,
            10,
            date(2026, 6, 16),
            time(19, 0),
            time(21, 0)
        )

        self.assertFalse(resultado)

    def test_alterar_com_conflito(self):
        resultado = alterar_reserva(
            1,
            4,
            5,
            date(2026, 6, 22),
            time(19, 0),
            time(21, 0)
        )
        self.assertFalse(resultado)

    def test_alterar_para_laboratorio_fica_pendente(self):
        resultado = alterar_reserva(
            1,
            4,
            6,
            date(2026, 6, 16),
            time(19, 0),
            time(21, 0)
        )

        self.assertTrue(resultado)

        reservas = pd.read_csv(self.arquivo_reservas, sep=";")
        reserva = reservas[reservas["idReserva"] == 1]

        self.assertEqual(reserva.iloc[0]["status"], "Pendente")

    def test_alterar_para_sala_comum_fica_confirmada(self):
        resultado = alterar_reserva(
            8,
            7,
            3,
            date(2026, 6, 16),
            time(19, 0),
            time(21, 0)
        )

        self.assertTrue(resultado)

        reservas = pd.read_csv(self.arquivo_reservas, sep=";")
        reserva = reservas[reservas["idReserva"] == 8]

        self.assertEqual(reserva.iloc[0]["status"], "Confirmada")   


# ---------------------------------------------------------------------------
# Reservas: aprovar / negar (autorização)
# ---------------------------------------------------------------------------

class TestAprovarNegarReserva(BaseAutorizacaoTest):

    def setUp(self):
        super().setUp()
        self.pendente = _garantir_reserva_pendente()

        if self.pendente is None:
            self.skipTest("É preciso ter ao menos uma reserva Confirmada ou Pendente no reservas.csv")

    # --- deve ser negado -------------------------------------------------

    def test_usuario_comum_nao_aprova(self):
        resultado = aprovar_reserva(self.pendente, self.id_comum)

        self.assertFalse(resultado)
        self.assertEqual(_status_reserva(self.pendente), "Pendente")

    def test_usuario_comum_nao_nega(self):
        resultado = negar_reserva(self.pendente, self.id_comum)

        self.assertFalse(resultado)
        self.assertEqual(_status_reserva(self.pendente), "Pendente")

    def test_admin_inativo_nao_aprova(self):
        _definir_status_usuario(self.id_admin, "Inativo")

        resultado = aprovar_reserva(self.pendente, self.id_admin)

        self.assertFalse(resultado)
        self.assertEqual(_status_reserva(self.pendente), "Pendente")

    def test_solicitante_inexistente_nao_aprova(self):
        self.assertFalse(aprovar_reserva(self.pendente, 99999))
        self.assertEqual(_status_reserva(self.pendente), "Pendente")

    def test_solicitante_none_nao_aprova(self):
        self.assertFalse(aprovar_reserva(self.pendente, None))
        self.assertEqual(_status_reserva(self.pendente), "Pendente")

    # --- deve funcionar --------------------------------------------------

    def test_admin_aprova_reserva_pendente(self):
        resultado = aprovar_reserva(self.pendente, self.id_admin)

        self.assertTrue(resultado)
        self.assertEqual(_status_reserva(self.pendente), "Confirmada")

    def test_admin_nega_reserva_pendente(self):
        resultado = negar_reserva(self.pendente, self.id_admin)

        self.assertTrue(resultado)
        self.assertEqual(_status_reserva(self.pendente), "Cancelada")

    def test_admin_nao_aprova_reserva_ja_confirmada(self):
        confirmada = _buscar_reserva("Confirmada")
        if confirmada is None:
            self.skipTest("Não há reserva Confirmada no reservas.csv")

        self.assertFalse(aprovar_reserva(confirmada, self.id_admin))

    def test_admin_aprova_reserva_inexistente(self):
        self.assertFalse(aprovar_reserva(99999, self.id_admin))


class TestUsuarioInativoReservas(BaseAutorizacaoTest):

    def setUp(self):
        super().setUp()
        reservas = carregar_reservas()
        minhas = reservas[(reservas["idUser"] == self.id_comum) & (reservas["status"] == "Confirmada")]
        if minhas.empty:
            self.skipTest("O usuário comum precisa ter uma reserva Confirmada no reservas.csv")
        self.id_reserva = int(minhas.iloc[0]["idReserva"])

    def test_usuario_inativo_nao_cria_reserva(self):
        _definir_status_usuario(self.id_comum, "Inativo")
        total_antes = len(carregar_reservas())

        resultado = criar_reserva(self.id_comum, 2, date(2026, 9, 16), time(19, 0), time(21, 0))

        self.assertIs(resultado, False)
        self.assertEqual(len(carregar_reservas()), total_antes)

    def test_usuario_inexistente_nao_cria_reserva(self):
        resultado = criar_reserva(99999, 2, date(2026, 9, 16), time(19, 0), time(21, 0))

        self.assertIs(resultado, False)

    def test_usuario_inativo_nao_cancela_reserva(self):
        _definir_status_usuario(self.id_comum, "Inativo")

        self.assertFalse(cancelar_reserva(self.id_reserva, self.id_comum))
        self.assertEqual(_status_reserva(self.id_reserva), "Confirmada")

    def test_usuario_inativo_nao_altera_reserva(self):
        _definir_status_usuario(self.id_comum, "Inativo")

        resultado = alterar_reserva(
            self.id_reserva, self.id_comum, 3, date(2026, 6, 16), time(19, 0), time(21, 0)
        )

        self.assertFalse(resultado)
        self.assertEqual(_status_reserva(self.id_reserva), "Confirmada")

    def test_usuario_ativo_continua_cancelando(self):
        self.assertTrue(cancelar_reserva(self.id_reserva, self.id_comum))
    
    def test_reserva_confirmada_em_lab_ou_auditorio_volta_para_pendente(self):
        # reserva 13 (usuário 1) está Confirmada no Lab01
        self.assertEqual(_status_reserva(13), "Confirmada")

        resultado = alterar_reserva(13, 1, 6, date(2026, 6, 8), time(19, 0), time(21, 0))

        self.assertTrue(resultado)
        self.assertEqual(_status_reserva(13), "Pendente")

    def test_reserva_pendente_so_volta_a_confirmada_com_admin(self):
        # usuário 1 é Aluno e usuário 5 é Admin
        alterar_reserva(13, 1, 6, date(2026, 6, 8), time(19, 0), time(21, 0))

        self.assertFalse(aprovar_reserva(13, 1))
        self.assertEqual(_status_reserva(13), "Pendente")

        self.assertTrue(aprovar_reserva(13, 5))
        self.assertEqual(_status_reserva(13), "Confirmada")

    def test_reserva_confirmada_movida_para_auditorio_fica_pendente(self):
        # reserva 3 (usuário 1) está Confirmada em sala comum; sala 11 é o auditório
        resultado = alterar_reserva(3, 1, 11, date(2026, 6, 16), time(19, 0), time(21, 0))

        self.assertTrue(resultado)
        self.assertEqual(_status_reserva(3), "Pendente")
            
if __name__ == "__main__":
    unittest.main()