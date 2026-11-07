
import subprocess

import pytest

import app.commit_actions as commit_actions

from app.approvals import solicitar_aprovacao
from app.git_manager import escrever_arquivo_local


CAMINHO_JAVA = "src/main/java/Calculadora.java"

CODIGO_JAVA = """
public class Calculadora {
    public int somar(int a, int b) {
        return a + b;
    }
}
"""


def git(repo, *argumentos):
    """Executa Git sem shell, no diretório informado."""

    resultado = subprocess.run(
        ["git", *argumentos],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )

    return resultado.stdout.strip()


@pytest.fixture
def ambiente(tmp_path):
    """
    Cria um repositório de trabalho e um
    remoto bare, ambos dentro do tmp_path.
    """

    repo = tmp_path / "projeto"
    remoto = tmp_path / "remoto.git"

    git(tmp_path, "init", "--bare", str(remoto))
    git(tmp_path, "init", "-b", "main", str(repo))

    git(repo, "config", "user.name", "Teste Aceitacao")
    git(
        repo,
        "config",
        "user.email",
        "teste@example.invalid",
    )
    git(repo, "config", "core.autocrlf", "false")

    escrever_arquivo_local(
        repo,
        "README.md",
        "# Repositorio de aceitacao\n",
    )

    git(repo, "add", "--", "README.md")
    git(repo, "commit", "-m", "commit inicial")

    git(repo, "remote", "add", "origin", str(remoto))
    git(repo, "push", "-u", "origin", "main")

    # Aponta o HEAD do remoto bare para main.
    git(
        remoto,
        "symbolic-ref",
        "HEAD",
        "refs/heads/main",
    )

    assert git(repo, "remote") == "origin"

    return repo, remoto


def head_remoto(remoto):
    return git(
        remoto,
        "rev-parse",
        "refs/heads/main",
    )


def criar_codigo_java(repo):
    return escrever_arquivo_local(
        repo,
        CAMINHO_JAVA,
        CODIGO_JAVA,
    )


def preparar_commit(monkeypatch, repo, respostas):
    """
    Usa o commit_actions.py real.

    Substitui somente a seleção do repositório,
    as aprovações e as chamadas ao git_manager
    por operações Git locais equivalentes.
    """

    respostas = iter(respostas)
    aprovacoes = []

    def aprovar(titulo, detalhes):
        aprovacoes.append(titulo)
        return next(respostas)

    monkeypatch.setattr(
        commit_actions,
        "selecionar_repositorio",
        lambda: "aceitacao/projeto-local",
    )

    monkeypatch.setattr(
        commit_actions,
        "clonar_repositorio",
        lambda nome: repo,
    )

    monkeypatch.setattr(
        commit_actions,
        "obter_branch_atual",
        lambda r: git(
            r, "branch", "--show-current"
        ),
    )

    monkeypatch.setattr(
        commit_actions,
        "listar_arquivos_stage",
        lambda r: git(
            r, "diff", "--cached", "--name-only"
        ).splitlines(),
    )

    monkeypatch.setattr(
        commit_actions,
        "listar_arquivos_para_commit",
        lambda r: [CAMINHO_JAVA],
    )

    monkeypatch.setattr(
        commit_actions,
        "escolher_arquivos",
        lambda arquivos: list(arquivos),
    )

    monkeypatch.setattr(
        commit_actions,
        "solicitar_aprovacao",
        aprovar,
    )

    monkeypatch.setattr(
        commit_actions,
        "adicionar_caminho_stage",
        lambda r, arquivo: git(
            r, "add", "--", arquivo
        ),
    )

    monkeypatch.setattr(
        commit_actions,
        "remover_caminho_stage",
        lambda r, arquivo: git(
            r, "restore", "--staged", "--", arquivo
        ),
    )

    monkeypatch.setattr(
        commit_actions,
        "obter_diff_stage",
        lambda r: git(r, "diff", "--cached"),
    )

    monkeypatch.setattr(
        commit_actions,
        "obter_head_commit",
        lambda r: git(r, "rev-parse", "HEAD"),
    )

    monkeypatch.setattr(
        commit_actions,
        "criar_commit_local",
        lambda r, mensagem: git(
            r, "commit", "-m", mensagem
        ),
    )

    monkeypatch.setattr(
        commit_actions,
        "obter_status_git",
        lambda r: git(r, "status", "--porcelain"),
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda mensagem: "feat: adiciona Calculadora",
    )

    return aprovacoes


# ----------------------------------------------
# 1. Fluxo completo autorizado
# ----------------------------------------------

def test_fluxo_aprovado_ate_remoto_local(
    ambiente,
    monkeypatch,
):
    repo, remoto = ambiente

    # Aprovação explícita da escrita no cenário.
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "s",
    )

    assert solicitar_aprovacao(
        "Criar classe Java",
        [CAMINHO_JAVA],
    ) is True

    criar_codigo_java(repo)

    head_inicial = git(repo, "rev-parse", "HEAD")
    remoto_inicial = head_remoto(remoto)

    aprovacoes = preparar_commit(
        monkeypatch,
        repo,
        [True, True],
    )

    commit_actions.criar_commit_controlado()

    assert len(aprovacoes) == 2
    assert git(repo, "rev-parse", "HEAD") != head_inicial
    assert git(repo, "status", "--porcelain") == ""

    # Commit local não publica automaticamente.
    assert head_remoto(remoto) == remoto_inicial

    # A publicação exige outra aprovação no cenário.
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "s",
    )

    if solicitar_aprovacao(
        "Publicar no remoto local de teste",
        ["Publicar a branch main"],
    ):
        git(repo, "push", "origin", "main")

    assert head_remoto(remoto) == git(
        repo, "rev-parse", "HEAD"
    )

    assert CAMINHO_JAVA in git(
        remoto, "ls-tree", "-r", "--name-only", "main"
    ).splitlines()


# ----------------------------------------------
# 2. Recusa de escrita no cenário
# ----------------------------------------------

def test_recusa_de_escrita_preserva_repositorio(
    ambiente,
    monkeypatch,
):
    repo, remoto = ambiente
    head_inicial = git(repo, "rev-parse", "HEAD")

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "n",
    )

    if solicitar_aprovacao(
        "Criar classe Java",
        [CAMINHO_JAVA],
    ):
        criar_codigo_java(repo)

    assert not (repo / CAMINHO_JAVA).exists()
    assert git(repo, "status", "--porcelain") == ""
    assert head_remoto(remoto) == head_inicial


# ----------------------------------------------
# 3. Recusa ao preparar staging
# ----------------------------------------------

def test_recusa_staging_preserva_alteracao(
    ambiente,
    monkeypatch,
):
    repo, remoto = ambiente
    criar_codigo_java(repo)

    head_inicial = git(repo, "rev-parse", "HEAD")

    aprovacoes = preparar_commit(
        monkeypatch,
        repo,
        [False],
    )

    commit_actions.criar_commit_controlado()

    assert len(aprovacoes) == 1
    assert git(repo, "rev-parse", "HEAD") == head_inicial
    assert git(repo, "diff", "--cached", "--name-only") == ""
    assert (repo / CAMINHO_JAVA).is_file()
    assert head_remoto(remoto) == head_inicial


# ----------------------------------------------
# 4. Recusa da aprovação final do commit
# ----------------------------------------------

def test_recusa_commit_limpa_staging(
    ambiente,
    monkeypatch,
):
    repo, remoto = ambiente
    criar_codigo_java(repo)

    head_inicial = git(repo, "rev-parse", "HEAD")

    aprovacoes = preparar_commit(
        monkeypatch,
        repo,
        [True, False],
    )

    commit_actions.criar_commit_controlado()

    assert len(aprovacoes) == 2
    assert git(repo, "rev-parse", "HEAD") == head_inicial
    assert git(repo, "diff", "--cached", "--name-only") == ""
    assert (repo / CAMINHO_JAVA).is_file()
    assert head_remoto(remoto) == head_inicial


# ----------------------------------------------
# 5. Recusa de publicação
# ----------------------------------------------

def test_recusa_publicacao_preserva_remoto(
    ambiente,
    monkeypatch,
):
    repo, remoto = ambiente
    criar_codigo_java(repo)

    remoto_inicial = head_remoto(remoto)

    preparar_commit(
        monkeypatch,
        repo,
        [True, True],
    )

    commit_actions.criar_commit_controlado()

    assert git(repo, "status", "--porcelain") == ""
    assert git(repo, "rev-parse", "HEAD") != remoto_inicial

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "n",
    )

    if solicitar_aprovacao(
        "Publicar no remoto local de teste",
        ["Publicar a branch main"],
    ):
        git(repo, "push", "origin", "main")

    # A recusa não altera o remoto.
    assert head_remoto(remoto) == remoto_inicial
