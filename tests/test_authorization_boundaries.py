
from types import SimpleNamespace

import pytest

import app.permissions as permissions
import app.commit_actions as commit_actions
import app.ai_dispatcher as dispatcher


REPO = "wjfo182/Estudos-Java"
OUTRO = "wjfo182/hello-world"


@pytest.fixture
def config_isolada(tmp_path, monkeypatch):
    """
    Substitui a configuração real por um
    arquivo temporário.
    """

    pasta = tmp_path / "config"
    arquivo = pasta / "authorized_repositories.json"

    monkeypatch.setattr(
        permissions,
        "CONFIG_DIR",
        pasta,
    )

    monkeypatch.setattr(
        permissions,
        "AUTHORIZED_FILE",
        arquivo,
    )

    return arquivo


def test_instalacao_nova_bloqueia(
    config_isolada,
):
    with pytest.raises(
        RuntimeError,
        match="não autorizado",
    ):
        permissions.exigir_repositorio_autorizado(
            REPO
        )


def test_repositorio_autorizado_passa(
    config_isolada,
):
    permissions.autorizar_repositorio(
        REPO
    )

    assert permissions.exigir_repositorio_autorizado(
        REPO
    ) is True


def test_autorizacao_nao_se_estende_a_outro_repo(
    config_isolada,
):
    permissions.autorizar_repositorio(
        REPO
    )

    with pytest.raises(
        RuntimeError,
        match="não autorizado",
    ):
        permissions.exigir_repositorio_autorizado(
            OUTRO
        )


def test_commit_bloqueado_antes_de_clonar(
    config_isolada,
    monkeypatch,
):
    monkeypatch.setattr(
        commit_actions,
        "selecionar_repositorio",
        lambda: REPO,
    )

    def clonagem_proibida(*args, **kwargs):
        pytest.fail(
            "Repositório não autorizado foi acessado."
        )

    monkeypatch.setattr(
        commit_actions,
        "clonar_repositorio",
        clonagem_proibida,
    )

    with pytest.raises(
        RuntimeError,
        match="não autorizado",
    ):
        commit_actions.criar_commit_controlado()


def test_dispatcher_bloqueia_antes_do_executor(
    config_isolada,
    monkeypatch,
):
    chamadas = []

    def executor_falso(*args):
        chamadas.append(args)

    monkeypatch.setitem(
        dispatcher.EXECUTORES,
        "melhorar_readme",
        executor_falso,
    )

    proposta = SimpleNamespace(
        tipo="melhorar_readme"
    )

    with pytest.raises(
        RuntimeError,
        match="não autorizado",
    ):
        dispatcher.executar_acao_proposta(
            REPO,
            {},
            proposta,
        )

    assert chamadas == []
