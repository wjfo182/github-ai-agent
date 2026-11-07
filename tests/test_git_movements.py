
import shutil
import subprocess
from types import SimpleNamespace

import pytest

import app.structure_actions as structure_actions

from app.git_manager import (
    mover_arquivo_local_sem_stage,
)


pytestmark = pytest.mark.skipif(
    shutil.which("git") is None,
    reason="Git não encontrado no ambiente.",
)


def git(repo, *argumentos):
    """
    Executa Git somente no repositório
    temporário fornecido pelo teste.
    """

    resultado = subprocess.run(
        ["git", *argumentos],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )

    return resultado.stdout


def criar_repositorio_temporario(tmp_path):
    """
    Cria um repositório Git isolado
    contendo src/Main.java.
    """

    git(tmp_path, "init", "-b", "main")

    git(
        tmp_path,
        "config",
        "user.name",
        "Teste Local",
    )

    git(
        tmp_path,
        "config",
        "user.email",
        "teste@example.invalid",
    )

    origem = tmp_path / "src/Main.java"

    origem.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    origem.write_text(
        "public class Main {}\n",
        encoding="utf-8",
    )

    git(
        tmp_path,
        "add",
        "--",
        "src/Main.java",
    )

    git(
        tmp_path,
        "commit",
        "-m",
        "commit inicial",
    )

    return tmp_path


def proposta():
    return SimpleNamespace(
        tipo="organizar_estrutura",
        titulo="Organizar Java",
        prioridade="media",
        motivo="Adequar estrutura Maven.",
    )


def movimentos():
    return [
        {
            "origem": "src/Main.java",
            "destino": "src/main/java/Main.java",
        }
    ]


# -----------------------------------------
# TESTE 1
# Move sem alterar o staging
# -----------------------------------------

def test_movimento_nao_adiciona_staging(
    tmp_path,
):
    repo = criar_repositorio_temporario(
        tmp_path
    )

    mover_arquivo_local_sem_stage(
        repo,
        "src/Main.java",
        "src/main/java/Main.java",
    )

    assert not (
        repo / "src/Main.java"
    ).exists()

    assert (
        repo / "src/main/java/Main.java"
    ).is_file()

    staged = git(
        repo,
        "diff",
        "--cached",
        "--name-only",
    )

    assert staged.strip() == ""

    status = git(
        repo,
        "status",
        "--porcelain",
        "--untracked-files=all",
    )

    assert " D src/Main.java" in status
    assert "?? src/main/java/Main.java" in status


# -----------------------------------------
# TESTE 2
# Permite commit depois do movimento
# -----------------------------------------

def test_commit_apos_movimento(
    tmp_path,
):
    repo = criar_repositorio_temporario(
        tmp_path
    )

    mover_arquivo_local_sem_stage(
        repo,
        "src/Main.java",
        "src/main/java/Main.java",
    )

    git(
        repo,
        "add",
        "--",
        "src/Main.java",
        "src/main/java/Main.java",
    )

    git(
        repo,
        "commit",
        "-m",
        "refactor: organiza estrutura",
    )

    status = git(
        repo,
        "status",
        "--porcelain",
    )

    assert status.strip() == ""

    assert (
        repo / "src/main/java/Main.java"
    ).is_file()


# -----------------------------------------
# TESTE 3
# Recusa não movimenta arquivos
# -----------------------------------------

def test_recusa_nao_movimenta(
    monkeypatch,
    tmp_path,
):
    repo = criar_repositorio_temporario(
        tmp_path
    )

    monkeypatch.setattr(
        structure_actions,
        "validar_organizacao_estrutura",
        lambda analise: movimentos(),
    )

    monkeypatch.setattr(
        structure_actions,
        "solicitar_aprovacao",
        lambda *args: False,
    )

    def clonagem_proibida(*args):
        pytest.fail(
            "Não deveria clonar após recusa."
        )

    monkeypatch.setattr(
        structure_actions,
        "clonar_repositorio",
        clonagem_proibida,
    )

    structure_actions.executar_organizar_estrutura(
        "teste/projeto",
        {"branch_analise": "main"},
        proposta(),
    )

    assert (
        repo / "src/Main.java"
    ).is_file()

    assert git(
        repo,
        "status",
        "--porcelain",
    ).strip() == ""


# -----------------------------------------
# TESTE 4
# Bloqueia repositório com alterações
# -----------------------------------------

def test_repositorio_sujo_bloqueia(
    monkeypatch,
    tmp_path,
):
    repo = criar_repositorio_temporario(
        tmp_path
    )

    (repo / "rascunho.txt").write_text(
        "Alteração local",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        structure_actions,
        "validar_organizacao_estrutura",
        lambda analise: movimentos(),
    )

    monkeypatch.setattr(
        structure_actions,
        "solicitar_aprovacao",
        lambda *args: True,
    )

    monkeypatch.setattr(
        structure_actions,
        "clonar_repositorio",
        lambda nome: str(repo),
    )

    with pytest.raises(
        RuntimeError,
        match="alterações locais",
    ):
        structure_actions.executar_organizar_estrutura(
            "teste/projeto",
            {"branch_analise": "main"},
            proposta(),
        )

    assert (
        repo / "src/Main.java"
    ).is_file()


# -----------------------------------------
# TESTE 5
# Impede sobrescrever destino
# -----------------------------------------

def test_destino_existente_bloqueia(
    tmp_path,
):
    repo = criar_repositorio_temporario(
        tmp_path
    )

    destino = (
        repo / "src/main/java/Main.java"
    )

    destino.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    destino.write_text(
        "// Arquivo existente\n",
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError,
        match="já existe",
    ):
        mover_arquivo_local_sem_stage(
            repo,
            "src/Main.java",
            "src/main/java/Main.java",
        )

    assert (
        repo / "src/Main.java"
    ).is_file()

    assert destino.read_text(
        encoding="utf-8",
    ) == "// Arquivo existente\n"
