"""reservas_service contra um MySQL de verdade."""
import datetime as dt

import pytest

from app.services import reservas_service, sala_service
from app.utils import relogio

H = dt.time  # atalho: H(8) == 08:00


def _status(banco, id_reserva):
    return banco.um("SELECT status_reserva FROM reservas WHERE id_reserva = %s", (id_reserva,))["status_reserva"]


# ---- criar_reserva ---------------------------------------------------------
def test_reserva_em_sala_comum_nasce_confirmada(banco, emails, id_aluno, id_sala, segunda):
    reserva = reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(8), H(9))

    assert reserva is not False
    linha = banco.um("SELECT * FROM reservas WHERE id_reserva = %s", (reserva.id,))
    assert linha["status_reserva"] == "Confirmada"
    assert linha["data_reserva"] == segunda
    assert (linha["hora_inicio"], linha["hora_fim"]) == (H(8), H(9))   # ida e volta da coluna TIME
    assert linha["criado_em"] == relogio.hoje()
    assert [e["destinatario"] for e in emails] == ["aluno@teste.com"]


def test_reserva_em_laboratorio_nasce_pendente(banco, emails, id_aluno, id_lab, segunda):
    reserva = reservas_service.criar_reserva(id_aluno, id_lab, segunda, H(8), H(9))

    assert reserva.esta_pendente
    assert _status(banco, reserva.id) == "Pendente"
    assert len(emails) == 1


def test_conflito_de_horario_retorna_false_e_nao_grava(banco, id_aluno, id_sala, segunda):
    reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(8), H(10))

    # outro aluno (sem prioridade) tentando sobrepor
    outro_aluno = banco.executar(
        "INSERT INTO usuarios (nome,email,telefone,papel,senha,status_usuario) VALUES ('B','b@teste.com','69999990000','Aluno','x','Ativo')"
    )
    assert reservas_service.criar_reserva(outro_aluno, id_sala, segunda, H(9), H(11)) is False
    assert banco.contar("reservas") == 1


def test_reservas_vizinhas_nao_conflitam(banco, id_aluno, id_professor, id_sala, segunda):
    """08-09 e 09-10 na mesma sala: o limite exato não é conflito."""
    primeira = reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(8), H(9))
    segunda_reserva = reservas_service.criar_reserva(id_professor, id_sala, segunda, H(9), H(10))

    assert primeira is not False and segunda_reserva is not False
    assert banco.contar("reservas", "status_reserva = 'Confirmada'") == 2


def test_reservas_de_dias_ou_salas_diferentes_nao_conflitam(id_aluno, id_sala, criar_sala_db, segunda):
    outra_sala = criar_sala_db("Sala")
    amanha = segunda + dt.timedelta(days=1)

    assert reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(8), H(9)) is not False
    assert reservas_service.criar_reserva(id_aluno, outra_sala, segunda, H(8), H(9)) is not False
    assert reservas_service.criar_reserva(id_aluno, id_sala, amanha, H(8), H(9)) is not False


def test_cancelada_libera_o_horario(id_aluno, id_sala, segunda):
    primeira = reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(8), H(9))
    reservas_service.cancelar_reserva(primeira.id, id_aluno)

    assert reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(8), H(9)) is not False


@pytest.mark.parametrize("status", ["Manutencao", "Indisponivel"])
def test_sala_que_nao_esta_disponivel_nao_recebe_reserva(banco, id_aluno, id_sala, segunda, status):
    banco.executar("UPDATE salas SET status_sala = %s WHERE id_sala = %s", (status, id_sala))

    assert reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(8), H(9)) is False
    assert banco.contar("reservas") == 0


def test_sala_oculta_nao_recebe_reserva(banco, id_admin, id_aluno, id_sala, segunda):
    sala_service.ocultar_sala(id_sala, id_admin)

    assert reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(8), H(9)) is False
    assert banco.contar("reservas") == 0


def test_usuario_inativo_nao_reserva(banco, criar_usuario_db, id_sala, segunda):
    inativo = criar_usuario_db(status="Inativo")

    assert reservas_service.criar_reserva(inativo, id_sala, segunda, H(8), H(9)) is False
    assert banco.contar("reservas") == 0


def test_regras_de_validacao_levantam_valueerror_e_nao_gravam(banco, id_aluno, id_sala, segunda, domingo):
    ontem = relogio.hoje() - dt.timedelta(days=1)

    with pytest.raises(ValueError):                       # domingo
        reservas_service.criar_reserva(id_aluno, id_sala, domingo, H(8), H(9))
    with pytest.raises(ValueError):                       # passado
        reservas_service.criar_reserva(id_aluno, id_sala, ontem, H(8), H(9))
    with pytest.raises(ValueError):                       # fora do expediente
        reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(6), H(8))
    with pytest.raises(ValueError):                       # menos de 30 min
        reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(8, 0), H(8, 15))
    with pytest.raises(ValueError):                       # mais de 4 horas
        reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(8), H(13))

    assert banco.contar("reservas") == 0


# ---- prioridade (professor x aluno) ----------------------------------------
def test_professor_assume_o_horario_do_aluno_e_cancela_a_reserva_dele(banco, id_aluno, id_professor, id_sala, segunda):
    do_aluno = reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(8), H(9))

    do_professor = reservas_service.criar_reserva(id_professor, id_sala, segunda, H(8), H(9))

    assert do_professor is not False
    assert _status(banco, do_professor.id) == "Confirmada"
    assert _status(banco, do_aluno.id) == "Cancelada"


def test_aluno_nao_assume_horario_de_professor(banco, id_aluno, id_professor, id_sala, segunda):
    reservas_service.criar_reserva(id_professor, id_sala, segunda, H(8), H(9))

    assert reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(8), H(9)) is False
    assert banco.contar("reservas") == 1


def test_professor_nao_assume_horario_de_outro_professor(banco, criar_usuario_db, id_professor, id_sala, segunda):
    outro = criar_usuario_db("Professor")
    reservas_service.criar_reserva(outro, id_sala, segunda, H(8), H(9))

    assert reservas_service.criar_reserva(id_professor, id_sala, segunda, H(8), H(9)) is False
    assert banco.contar("reservas") == 1


def test_professor_no_laboratorio_so_substitui_o_aluno_quando_o_admin_aprova(
        banco, id_admin, id_aluno, id_professor, id_lab, segunda):
    do_aluno = reservas_service.criar_reserva(id_aluno, id_lab, segunda, H(8), H(9))
    do_professor = reservas_service.criar_reserva(id_professor, id_lab, segunda, H(8), H(9))

    # enquanto está pendente, nada muda para o aluno
    assert _status(banco, do_professor.id) == "Pendente"
    assert _status(banco, do_aluno.id) == "Pendente"

    assert reservas_service.aprovar_reserva(do_professor.id, id_admin) is not False

    assert _status(banco, do_professor.id) == "Confirmada"
    assert _status(banco, do_aluno.id) == "Cancelada"


# ---- cancelar / aprovar / negar --------------------------------------------
def test_cancelar_reserva_so_pelo_dono_e_so_se_ativa(banco, id_aluno, id_professor, id_sala, segunda):
    reserva = reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(8), H(9))

    assert reservas_service.cancelar_reserva(reserva.id, id_professor) is False   # não é o dono
    assert _status(banco, reserva.id) == "Confirmada"

    assert reservas_service.cancelar_reserva(reserva.id, id_aluno) is not False
    assert _status(banco, reserva.id) == "Cancelada"

    assert reservas_service.cancelar_reserva(reserva.id, id_aluno) is False       # já cancelada
    assert reservas_service.cancelar_reserva(9999, id_aluno) is False


def test_admin_aprova_reserva_pendente_e_o_dono_e_avisado(banco, emails, id_admin, id_aluno, id_lab, segunda):
    reserva = reservas_service.criar_reserva(id_aluno, id_lab, segunda, H(8), H(9))
    emails.clear()

    assert reservas_service.aprovar_reserva(reserva.id, id_admin) is not False

    assert _status(banco, reserva.id) == "Confirmada"
    assert [e["destinatario"] for e in emails] == ["aluno@teste.com"]


def test_admin_nega_reserva_pendente_e_o_dono_e_avisado(banco, emails, id_admin, id_aluno, id_lab, segunda):
    reserva = reservas_service.criar_reserva(id_aluno, id_lab, segunda, H(8), H(9))
    emails.clear()

    assert reservas_service.negar_reserva(reserva.id, id_admin) is not False

    assert _status(banco, reserva.id) == "Cancelada"
    assert [e["destinatario"] for e in emails] == ["aluno@teste.com"]


def test_aprovar_e_negar_so_valem_para_admin_e_para_reserva_pendente(banco, id_admin, id_aluno, id_sala, id_lab, segunda):
    pendente = reservas_service.criar_reserva(id_aluno, id_lab, segunda, H(8), H(9))
    confirmada = reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(8), H(9))

    assert reservas_service.aprovar_reserva(pendente.id, id_aluno) is False      # não é admin
    assert reservas_service.negar_reserva(pendente.id, id_aluno) is False
    assert reservas_service.aprovar_reserva(confirmada.id, id_admin) is False    # não está pendente
    assert reservas_service.negar_reserva(confirmada.id, id_admin) is False
    assert reservas_service.aprovar_reserva(9999, id_admin) is False
    assert _status(banco, pendente.id) == "Pendente"
    assert _status(banco, confirmada.id) == "Confirmada"


# ---- alterar_reserva -------------------------------------------------------
def test_alterar_horario_da_propria_reserva(banco, id_aluno, id_sala, segunda):
    reserva = reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(8), H(9))

    # sobrepõe o próprio horário antigo: não pode contar como conflito consigo mesma
    resultado = reservas_service.alterar_reserva(reserva.id, id_aluno, id_sala, segunda, H(8, 30), H(9, 30))

    assert resultado is not False
    linha = banco.um("SELECT hora_inicio, hora_fim FROM reservas WHERE id_reserva = %s", (reserva.id,))
    assert (linha["hora_inicio"], linha["hora_fim"]) == (H(8, 30), H(9, 30))


def test_alterar_para_horario_ocupado_retorna_false_e_mantem_o_original(banco, id_aluno, id_professor, id_sala, segunda):
    reservas_service.criar_reserva(id_professor, id_sala, segunda, H(10), H(11))
    do_aluno = reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(8), H(9))

    assert reservas_service.alterar_reserva(do_aluno.id, id_aluno, id_sala, segunda, H(10), H(11)) is False

    linha = banco.um("SELECT hora_inicio FROM reservas WHERE id_reserva = %s", (do_aluno.id,))
    assert linha["hora_inicio"] == H(8)


def test_so_o_dono_altera_a_reserva(id_aluno, id_professor, id_sala, segunda):
    reserva = reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(8), H(9))

    assert reservas_service.alterar_reserva(reserva.id, id_professor, id_sala, segunda, H(10), H(11)) is False


# ---- consultas com JOIN ----------------------------------------------------
def test_consultas_de_reservas_trazem_nomes_e_horarios_como_time(id_admin, id_aluno, id_sala, id_lab, segunda):
    reservas_service.criar_reserva(id_aluno, id_sala, segunda, H(8), H(9))
    reservas_service.criar_reserva(id_aluno, id_lab, segunda, H(10), H(11))

    pendentes = reservas_service.consultar_reservas_pendentes(id_admin)
    proxima = reservas_service.consultar_proxima_reserva(id_aluno, relogio.hoje())
    do_aluno = reservas_service.consultar_reservas_usuario(id_aluno)

    assert [(p["nome_sala"], p["nome_usuario"], p["hora_inicio"]) for p in pendentes] == [("Lab01", "Aluno Teste", H(10))]
    assert (proxima["nome_sala"], proxima["hora_inicio"]) == ("Sala01", H(8))
    assert [r["hora_inicio"] for r in do_aluno] == [H(10), H(8)]            # mais recente primeiro
    assert all(r["pode_alterar"] for r in do_aluno)


def test_consultar_pendentes_exige_admin(id_aluno):
    with pytest.raises(PermissionError):
        reservas_service.consultar_reservas_pendentes(id_aluno)
