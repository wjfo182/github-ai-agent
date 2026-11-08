
import pytest

import app.permissions as permissions
import app.push_actions as push_actions


REPO = "wjfo182/github-ai-agent-homologacao"
OUTRO = "wjfo182/hello-world"


@pytest.fixture
def ambiente_push(monkeypatch, tmp_path):
    """
    Simula um ambiente de publicação.

    As permissões são armazenadas em um
    diretório temporário.

    Não executa Git, push ou chamadas ao GitHub.
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

    chamadas = []

    # Simular seleção
    monkeypatch.setattr(
        push_actions,
        "selecionar_repositorio",
        lambda: REPO,
    )

    # Registrar tentativa de acesso
    def clonar(nome):
        chamadas.append(("clonar", nome))
        return tmp_path

    monkeypatch.setattr(
        push_actions,
        "clonar_repositorio",
        clonar,
    )

    monkeypatch.setattr(
        push_actions,
        "validar_destino_origin",
        lambda repo, nome: True,
    )

    monkeypatch.setattr(
        push_actions,
        "obter_branch_atual",
        lambda repo: "main",
    )

    monkeypatch.setattr(
        push_actions,
        "repositorio_esta_limpo",
        lambda repo: True,
    )

    monkeypatch.setattr(
        push_actions,
        "atualizar_todas_referencias",
        lambda repo: None,
    )

    monkeypatch.setattr(
        push_actions,
        "branch_remota_existe",
        lambda repo, branch: True,
    )

    monkeypatch.setattr(
        push_actions,
        "obter_sincronizacao",
        lambda repo, branch: {
            "frente": 1,
            "atras": 0,
        },
    )

    monkeypatch.setattr(
        push_actions,
        "obter_commits_para_push",
        lambda repo, branch: "abc123",
    )

    monkeypatch.setattr(
        push_actions,
        "obter_historico_recente",
        lambda repo, limite=10: "abc123",
    )

    # Por padrão, o usuário recusa.
    monkeypatch.setattr(
        push_actions,
        "solicitar_aprovacao",
        lambda *args: False,
    )

    # Simular publicação existente
    def executar_push_falso(repo, branch):
        chamadas.append(("push", branch))
        return "Push simulado"

    monkeypatch.setattr(
        push_actions,
        "executar_push",
        executar_push_falso,
    )

    # Simular publicação de nova branch
    def publicar_branch_falsa(repo, branch):
        chamadas.append(("nova_branch", branch))
        return "Nova branch simulada"

    monkeypatch.setattr(
        push_actions,
        "publicar_nova_branch",
        publicar_branch_falsa,
    )

    return {
        "arquivo": arquivo,
        "chamadas": chamadas,
    }


# ---------------------------------------------
# TESTE 1 - Instalação sem autorizações
# ---------------------------------------------

def test_push_bloqueado_sem_configuracao(
    ambiente_push,
):
    with pytest.raises(
        RuntimeError,
        match="não autorizado",
    ):
        push_actions.publicar_branch_atual()

    assert ambiente_push["chamadas"] == []


# ---------------------------------------------
# TESTE 2 - Outro repositório autorizado
# ---------------------------------------------

def test_push_bloqueado_repo_nao_autorizado(
    ambiente_push,
):
    permissions.autorizar_repositorio(OUTRO)

    with pytest.raises(
        RuntimeError,
        match="não autorizado",
    ):
        push_actions.publicar_branch_atual()

    assert ambiente_push["chamadas"] == []


# ---------------------------------------------
# TESTE 3 - Configuração corrompida
# ---------------------------------------------

def test_push_bloqueado_json_invalido(
    ambiente_push,
):
    arquivo = ambiente_push["arquivo"]

    arquivo.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    arquivo.write_text(
        "{json invalido",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError):
        push_actions.publicar_branch_atual()

    assert ambiente_push["chamadas"] == []


# ---------------------------------------------
# TESTE 4 - Recusa de push na branch existente
# ---------------------------------------------

def test_recusa_push_branch_existente(
    ambiente_push,
):
    permissions.autorizar_repositorio(REPO)

    push_actions.publicar_branch_atual()

    assert (
        "push",
        "main",
    ) not in ambiente_push["chamadas"]


# ---------------------------------------------
# TESTE 5 - Aprovação de push existente
# ---------------------------------------------

def test_aprovacao_push_branch_existente(
    ambiente_push,
    monkeypatch,
):
    permissions.autorizar_repositorio(REPO)

    monkeypatch.setattr(
        push_actions,
        "solicitar_aprovacao",
        lambda *args: True,
    )

    push_actions.publicar_branch_atual()

    assert ambiente_push["chamadas"].count(
        ("push", "main")
    ) == 1


# ---------------------------------------------
# TESTE 6 - Recusa de nova branch
# ---------------------------------------------

def test_recusa_publicacao_nova_branch(
    ambiente_push,
    monkeypatch,
):
    permissions.autorizar_repositorio(REPO)

    monkeypatch.setattr(
        push_actions,
        "branch_remota_existe",
        lambda repo, branch: False,
    )

    push_actions.publicar_branch_atual()

    assert (
        "nova_branch",
        "main",
    ) not in ambiente_push["chamadas"]


# ---------------------------------------------
# TESTE 7 - Aprovação de nova branch
# ---------------------------------------------

def test_aprovacao_publicacao_nova_branch(
    ambiente_push,
    monkeypatch,
):
    permissions.autorizar_repositorio(REPO)

    monkeypatch.setattr(
        push_actions,
        "branch_remota_existe",
        lambda repo, branch: False,
    )

    monkeypatch.setattr(
        push_actions,
        "solicitar_aprovacao",
        lambda *args: True,
    )

    push_actions.publicar_branch_atual()

    assert ambiente_push["chamadas"].count(
        ("nova_branch", "main")
    ) == 1
