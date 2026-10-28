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


# [NOVO] Helpers dos testes do fluxo de aprovação/negação e da regra 13
def _forcar_status_reserva(id_reserva, status):
    """Grava o status direto no CSV para montar o estado inicial do teste.
    O CSV é restaurado pelo cleanup da BaseCSVTest."""
    reservas = carregar_reservas()
    reservas.loc[reservas["idReserva"] == id_reserva, "status"] = status
    reservas.to_csv(DATA_DIR / "reservas.csv", sep=";", index=False)


def _dono_da_reserva(id_reserva):
    reservas = carregar_reservas()
    return int(reservas[reservas["idReserva"] == id_reserva].iloc[0]["idUser"])


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


# ---------------------------------------------------------------------------
# [NOVO] Fluxo de aprovação/negação do Admin (Pendente -> Confirmada / Cancelada)
# ---------------------------------------------------------------------------

ID_RESERVA_INEXISTENTE = 99999


class TestFluxoAprovacaoAdmin(BaseAutorizacaoTest):

    ACOES = (("aprovar", aprovar_reserva), ("negar", negar_reserva))

    def setUp(self):
        super().setUp()
        self.alvo = _garantir_reserva_pendente()

        if self.alvo is None:
            self.skipTest("É preciso ter ao menos uma reserva Confirmada ou Pendente no reservas.csv")

    def _assert_so_o_status_mudou(self, antes, depois, id_reserva, novo_status):
        """A reserva alvo muda só a coluna status; todas as outras linhas ficam idênticas."""
        self.assertEqual(len(antes), len(depois))

        alvo_antes = antes[antes["idReserva"] == id_reserva].reset_index(drop=True)
        alvo_depois = depois[depois["idReserva"] == id_reserva].reset_index(drop=True)

        self.assertEqual(alvo_depois.iloc[0]["status"], novo_status)
        pd.testing.assert_frame_equal(
            alvo_antes.drop(columns="status"),
            alvo_depois.drop(columns="status"),
        )

        outras_antes = antes[antes["idReserva"] != id_reserva].reset_index(drop=True)
        outras_depois = depois[depois["idReserva"] != id_reserva].reset_index(drop=True)
        pd.testing.assert_frame_equal(outras_antes, outras_depois)

    # --- Pendente -> Confirmada / Cancelada, sem efeito colateral -----------

    def test_aprovar_pendente_muda_so_a_reserva_alvo(self):
        self.assertEqual(_status_reserva(self.alvo), "Pendente")
        antes = carregar_reservas()

        self.assertTrue(aprovar_reserva(self.alvo, self.id_admin))

        self._assert_so_o_status_mudou(antes, carregar_reservas(), self.alvo, "Confirmada")

    def test_negar_pendente_muda_so_a_reserva_alvo(self):
        self.assertEqual(_status_reserva(self.alvo), "Pendente")
        antes = carregar_reservas()

        self.assertTrue(negar_reserva(self.alvo, self.id_admin))

        self._assert_so_o_status_mudou(antes, carregar_reservas(), self.alvo, "Cancelada")

    # --- Confirmada e Cancelada são estados finais -------------------------

    def test_aprovar_e_negar_a_partir_de_estado_final_sao_rejeitados(self):
        for status_inicial in ("Confirmada", "Cancelada"):
            for nome, acao in self.ACOES:
                with self.subTest(status_inicial=status_inicial, acao=nome):
                    _forcar_status_reserva(self.alvo, status_inicial)
                    antes = carregar_reservas()

                    resultado = acao(self.alvo, self.id_admin)

                    self.assertFalse(resultado)
                    pd.testing.assert_frame_equal(antes, carregar_reservas())

    def test_aprovar_duas_vezes_a_segunda_e_rejeitada(self):
        self.assertTrue(aprovar_reserva(self.alvo, self.id_admin))
        self.assertFalse(aprovar_reserva(self.alvo, self.id_admin))
        self.assertEqual(_status_reserva(self.alvo), "Confirmada")

    def test_negar_duas_vezes_a_segunda_e_rejeitada(self):
        self.assertTrue(negar_reserva(self.alvo, self.id_admin))
        self.assertFalse(negar_reserva(self.alvo, self.id_admin))
        self.assertEqual(_status_reserva(self.alvo), "Cancelada")

    def test_reserva_negada_nao_pode_ser_aprovada_depois(self):
        self.assertTrue(negar_reserva(self.alvo, self.id_admin))

        self.assertFalse(aprovar_reserva(self.alvo, self.id_admin))
        self.assertEqual(_status_reserva(self.alvo), "Cancelada")

    def test_reserva_aprovada_nao_pode_ser_negada_depois(self):
        self.assertTrue(aprovar_reserva(self.alvo, self.id_admin))

        self.assertFalse(negar_reserva(self.alvo, self.id_admin))
        self.assertEqual(_status_reserva(self.alvo), "Confirmada")

    # --- Reserva inexistente ------------------------------------------------

    def test_reserva_inexistente_nao_aprova_nem_nega_e_nao_altera_o_csv(self):
        for nome, acao in self.ACOES:
            with self.subTest(acao=nome):
                antes = carregar_reservas()

                resultado = acao(ID_RESERVA_INEXISTENTE, self.id_admin)

                self.assertFalse(resultado)
                pd.testing.assert_frame_equal(antes, carregar_reservas())

    # --- Quem não pode aprovar/negar (cobre também o "negar", que faltava) --

    def test_solicitante_sem_permissao_nao_aprova_nem_nega(self):
        solicitantes = {
            "usuario comum": self.id_comum,
            "inexistente": 99999,
            "None": None,
        }

        for rotulo, id_solicitante in solicitantes.items():
            for nome, acao in self.ACOES:
                with self.subTest(solicitante=rotulo, acao=nome):
                    antes = carregar_reservas()

                    resultado = acao(self.alvo, id_solicitante)

                    self.assertFalse(resultado)
                    pd.testing.assert_frame_equal(antes, carregar_reservas())

    def test_admin_inativo_nao_aprova_nem_nega(self):
        _definir_status_usuario(self.id_admin, "Inativo")

        for nome, acao in self.ACOES:
            with self.subTest(acao=nome):
                antes = carregar_reservas()

                resultado = acao(self.alvo, self.id_admin)

                self.assertFalse(resultado)
                pd.testing.assert_frame_equal(antes, carregar_reservas())


# ---------------------------------------------------------------------------
# [NOVO] Regra 13: alterar uma reserva envolvendo laboratório ou auditório
# devolve o status para Pendente, mesmo que estivesse Confirmada.
#
# Ajuste as constantes abaixo se o seu seed for diferente. Os valores foram
# tirados dos testes que já existem neste arquivo (sala 3 = comum, 6 = laboratório,
# 11 = auditório, 7 = manutenção, 10 = indisponível; reserva 3 = Confirmada em
# sala comum; reserva 13 = Confirmada em laboratório).
# ---------------------------------------------------------------------------

SALA_COMUM = 3
SALA_LABORATORIO = 6
SALA_AUDITORIO = 11
SALA_MANUTENCAO = 7
SALA_INDISPONIVEL = 10
SALA_INEXISTENTE = 999

RESERVA_CONFIRMADA_EM_SALA_COMUM = 3
RESERVA_CONFIRMADA_EM_LABORATORIO = 13

DATA_NOVA = date(2026, 6, 16)
INICIO_NOVO = time(19, 0)
FIM_NOVO = time(21, 0)


class TestRegra13AlteracaoVoltaParaPendente(BaseAutorizacaoTest):

    def _alterar(self, id_reserva, id_sala):
        """Altera a reserva em nome do próprio dono (o ID vem do CSV)."""
        return alterar_reserva(
            id_reserva, _dono_da_reserva(id_reserva), id_sala,
            DATA_NOVA, INICIO_NOVO, FIM_NOVO,
        )

    def _resetar_csvs(self):
        """Volta os CSVs ao estado do início do teste (para usar entre subTests)."""
        for nome in self.ARQUIVOS:
            origem = DATA_DIR / nome
            shutil.copy(DATA_DIR / f"{origem.stem}_backup.csv", origem)

    # --- Tabela da regra: status inicial x tipo da sala de destino ---------

    def test_status_apos_alteracao_depende_do_tipo_da_sala_de_destino(self):
        casos = [
            # (reserva, status inicial, sala de destino, status esperado)
            (RESERVA_CONFIRMADA_EM_SALA_COMUM, "Confirmada", SALA_COMUM, "Confirmada"),
            (RESERVA_CONFIRMADA_EM_SALA_COMUM, "Confirmada", SALA_LABORATORIO, "Pendente"),
            (RESERVA_CONFIRMADA_EM_SALA_COMUM, "Confirmada", SALA_AUDITORIO, "Pendente"),
            (RESERVA_CONFIRMADA_EM_SALA_COMUM, "Pendente", SALA_COMUM, "Confirmada"),
            (RESERVA_CONFIRMADA_EM_SALA_COMUM, "Pendente", SALA_LABORATORIO, "Pendente"),
            (RESERVA_CONFIRMADA_EM_SALA_COMUM, "Pendente", SALA_AUDITORIO, "Pendente"),
            # já em laboratório e continua em laboratório (só muda data/horário)
            (RESERVA_CONFIRMADA_EM_LABORATORIO, "Confirmada", SALA_LABORATORIO, "Pendente"),
        ]

        for reserva, status_inicial, sala, esperado in casos:
            with self.subTest(reserva=reserva, inicial=status_inicial, sala=sala):
                self._resetar_csvs()
                _forcar_status_reserva(reserva, status_inicial)

                resultado = self._alterar(reserva, sala)

                self.assertTrue(resultado)
                self.assertEqual(_status_reserva(reserva), esperado)

    # --- Alteração rejeitada não pode mexer no status ----------------------

    def test_alteracao_rejeitada_nao_tira_a_reserva_de_confirmada(self):
        for sala in (SALA_MANUTENCAO, SALA_INDISPONIVEL, SALA_INEXISTENTE):
            with self.subTest(sala=sala):
                self._resetar_csvs()
                self.assertEqual(_status_reserva(RESERVA_CONFIRMADA_EM_SALA_COMUM), "Confirmada")
                antes = carregar_reservas()

                resultado = self._alterar(RESERVA_CONFIRMADA_EM_SALA_COMUM, sala)

                self.assertFalse(resultado)
                pd.testing.assert_frame_equal(antes, carregar_reservas())

    # --- Ciclo completo: Confirmada -> (regra 13) Pendente -> decisão Admin --

    def test_alteracao_para_laboratorio_e_depois_aprovada_volta_a_confirmada(self):
        reserva = RESERVA_CONFIRMADA_EM_SALA_COMUM

        self.assertTrue(self._alterar(reserva, SALA_LABORATORIO))
        self.assertEqual(_status_reserva(reserva), "Pendente")

        self.assertTrue(aprovar_reserva(reserva, self.id_admin))
        self.assertEqual(_status_reserva(reserva), "Confirmada")

    def test_alteracao_para_laboratorio_e_depois_negada_vira_cancelada(self):
        reserva = RESERVA_CONFIRMADA_EM_SALA_COMUM

        self.assertTrue(self._alterar(reserva, SALA_LABORATORIO))
        self.assertEqual(_status_reserva(reserva), "Pendente")

        self.assertTrue(negar_reserva(reserva, self.id_admin))
        self.assertEqual(_status_reserva(reserva), "Cancelada")

        # e uma reserva negada não pode mais ser alterada para "escapar" do estado
        self.assertFalse(self._alterar(reserva, SALA_COMUM))
        self.assertEqual(_status_reserva(reserva), "Cancelada")

    def test_dono_nao_aprova_a_propria_reserva_que_voltou_para_pendente(self):
        reserva = RESERVA_CONFIRMADA_EM_SALA_COMUM
        dono = _dono_da_reserva(reserva)
        usuarios = carregar_usuarios()
        if usuarios[usuarios["idUser"] == dono].iloc[0]["role"] == "Admin":
            self.skipTest("O dono da reserva é Admin; o teste exige um dono sem perfil Admin")

        self.assertTrue(self._alterar(reserva, SALA_AUDITORIO))
        self.assertEqual(_status_reserva(reserva), "Pendente")

        self.assertFalse(aprovar_reserva(reserva, dono))
        self.assertEqual(_status_reserva(reserva), "Pendente")


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