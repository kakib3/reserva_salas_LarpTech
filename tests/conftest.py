"""Configuração compartilhada dos testes unitários."""
import pytest

from app.models import conexao


@pytest.fixture(autouse=True)
def _bloquear_banco_real(monkeypatch):
    """Nenhum teste unitário pode abrir conexão com o banco real.

    Os services chamam `conectar_banco()`, que lê `st.secrets`. Numa máquina com um
    `secrets.toml` de produção, um mock esquecido faria o teste conectar na produção
    (e erros de notificação são engolidos, então ninguém perceberia).
    Se isso acontecer, este bloqueio faz o teste falhar de forma barulhenta.
    """

    def proibido(*args, **kwargs):
        raise RuntimeError(
            "Teste unitário tentou abrir conexão com o banco real. "
            "Faça monkeypatch de `conectar_banco` no service."
        )

    monkeypatch.setattr(conexao, "obter_pool", proibido)
