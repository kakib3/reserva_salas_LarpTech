import pytest

from app.models.constantes import PapelUsuario, StatusReserva
from app.services.reservas_service import (
    _cancelar_reservas_substituidas,
    _resolver_prioridade,
)


def _conflito(id_reserva, papel):
    return {"id_reserva": id_reserva, "papel": papel}


# ---------------------------------------------------------------------------
# Regra de prioridade: Professor > Aluno; entre os demais, quem reservou primeiro
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("papel", [PapelUsuario.ALUNO, PapelUsuario.PROFESSOR, PapelUsuario.ADMIN, None])
def test_sem_conflito_libera_qualquer_papel(papel):
    assert _resolver_prioridade(papel, []) == (True, [])


def test_professor_assume_horario_de_aluno():
    conflitos = [_conflito(10, PapelUsuario.ALUNO)]

    assert _resolver_prioridade(PapelUsuario.PROFESSOR, conflitos) == (True, [10])


def test_professor_assume_horario_de_varios_alunos():
    conflitos = [_conflito(10, PapelUsuario.ALUNO), _conflito(11, PapelUsuario.ALUNO)]

    assert _resolver_prioridade(PapelUsuario.PROFESSOR, conflitos) == (True, [10, 11])


def test_dois_professores_disputando_vale_o_primeiro_a_reservar():
    conflitos = [_conflito(10, PapelUsuario.PROFESSOR)]

    assert _resolver_prioridade(PapelUsuario.PROFESSOR, conflitos) == (False, [])


def test_professor_nao_assume_se_houver_professor_entre_os_conflitos():
    conflitos = [_conflito(10, PapelUsuario.ALUNO), _conflito(11, PapelUsuario.PROFESSOR)]

    assert _resolver_prioridade(PapelUsuario.PROFESSOR, conflitos) == (False, [])


def test_professor_nao_assume_horario_de_admin():
    conflitos = [_conflito(10, PapelUsuario.ADMIN)]

    assert _resolver_prioridade(PapelUsuario.PROFESSOR, conflitos) == (False, [])


def test_conflito_sem_dono_conhecido_nao_pode_ser_substituido():
    conflitos = [_conflito(10, None)]

    assert _resolver_prioridade(PapelUsuario.PROFESSOR, conflitos) == (False, [])


@pytest.mark.parametrize("dono", [PapelUsuario.ALUNO, PapelUsuario.PROFESSOR])
def test_aluno_nunca_assume_horario(dono):
    conflitos = [_conflito(10, dono)]

    assert _resolver_prioridade(PapelUsuario.ALUNO, conflitos) == (False, [])


def test_admin_nao_tem_prioridade_sobre_aluno():
    conflitos = [_conflito(10, PapelUsuario.ALUNO)]

    assert _resolver_prioridade(PapelUsuario.ADMIN, conflitos) == (False, [])


# ---------------------------------------------------------------------------
# Cancelamento das reservas substituídas
# ---------------------------------------------------------------------------

class _CursorFalso:
    def __init__(self):
        self.chamadas = []

    def execute(self, sql, valores=None):
        self.chamadas.append((sql, valores))


def test_cancelar_sem_ids_nao_executa_nada():
    cursor = _CursorFalso()

    _cancelar_reservas_substituidas(cursor, [])

    assert cursor.chamadas == []


def test_cancelar_executa_um_update_apenas_nas_reservas_ativas():
    cursor = _CursorFalso()

    _cancelar_reservas_substituidas(cursor, [10, 11])

    assert len(cursor.chamadas) == 1
    sql, valores = cursor.chamadas[0]
    assert "UPDATE reservas SET status_reserva" in sql
    assert "IN (%s, %s)" in sql
    assert valores == (
        StatusReserva.CANCELADA, 10, 11,
        StatusReserva.CONFIRMADA, StatusReserva.PENDENTE,
    )
