
import shutil
import subprocess

import pytest

from app.git_manager import (
    escrever_arquivo_local,
    mover_arquivo_local_sem_stage,
)


pytestmark = pytest.mark.skipif(
    shutil.which("git") is None,
    reason="Git não instalado.",
)


def git(repo, *argumentos):
    """
    Executa Git somente no diretório
    temporário informado.
    """
    resultado = subprocess.run(
        ["git", *argumentos],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )

    return resultado.stdout.strip()


@pytest.fixture
def repo_temporario(tmp_path):
    """
    Cria um repositório Git local isolado,
    sem conexão com o GitHub.
    """

    git(tmp_path, "init")

    git(
        tmp_path,
        "config",
        "user.name",
        "Agente Teste",
    )

    git(
        tmp_path,
        "config",
        "user.email",
        "teste@example.invalid",
    )

    escrever_arquivo_local(
        tmp_path,
        "README.md",
        "# Projeto de teste\n",
    )

    git(tmp_path, "add", "--", "README.md")

    git(
        tmp_path,
        "commit",
        "-m",
        "commit inicial",
    )

    return tmp_path


# -------------------------------------------
# TESTE 1 - Escrita, staging e commit
# -------------------------------------------

def test_ciclo_completo_de_commit(
    repo_temporario,
):
    repo = repo_temporario

    escrever_arquivo_local(
        repo,
        "src/test/java/CalculadoraTest.java",
        "class CalculadoraTest {}\n",
    )

    # A escrita não deve alterar o staging.
    assert git(
        repo,
        "diff",
        "--cached",
        "--name-only",
    ) == ""

    # Simula a preparação explícita do commit.
    git(
        repo,
        "add",
        "--",
        "src/test/java/CalculadoraTest.java",
    )

    arquivos_preparados = git(
        repo,
        "diff",
        "--cached",
        "--name-only",
    )

    assert (
        "src/test/java/CalculadoraTest.java"
        in arquivos_preparados
    )

    git(
        repo,
        "commit",
        "-m",
        "test: adiciona teste Java",
    )

    assert git(
        repo,
        "status",
        "--porcelain",
    ) == ""

    assert git(
        repo,
        "log",
        "-1",
        "--format=%s",
    ) == "test: adiciona teste Java"

    # O repositório temporário não possui remoto.
    assert git(repo, "remote") == ""


# -------------------------------------------
# TESTE 2 - Movimentação e commit
# -------------------------------------------

def test_movimentacao_com_commit(
    repo_temporario,
):
    repo = repo_temporario

    escrever_arquivo_local(
        repo,
        "src/Main.java",
        "public class Main {}\n",
    )

    git(
        repo,
        "add",
        "--",
        "src/Main.java",
    )

    git(
        repo,
        "commit",
        "-m",
        "feat: adiciona Main",
    )

    mover_arquivo_local_sem_stage(
        repo,
        "src/Main.java",
        "src/main/java/Main.java",
    )

    assert git(
        repo,
        "diff",
        "--cached",
        "--name-only",
    ) == ""

    git(
        repo,
        "add",
        "-A",
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

    arquivos = git(
        repo,
        "ls-files",
    ).splitlines()

    assert "src/main/java/Main.java" in arquivos
    assert "src/Main.java" not in arquivos

    assert git(
        repo,
        "status",
        "--porcelain",
    ) == ""


# -------------------------------------------
# TESTE 3 - Arquivo alterado após revisão
# -------------------------------------------

def test_bloqueia_arquivo_modificado(
    repo_temporario,
):
    repo = repo_temporario

    readme = repo / "README.md"

    conteudo_revisado = readme.read_text(
        encoding="utf-8"
    )

    # Simula outro processo modificando o arquivo
    # depois da análise do agente.
    readme.write_text(
        "# Modificado externamente\n",
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError,
        match="mudou",
    ):
        escrever_arquivo_local(
            repo,
            "README.md",
            "# Nova versão gerada pela IA\n",
            sobrescrever=True,
            conteudo_esperado=conteudo_revisado,
        )

    assert readme.read_text(
        encoding="utf-8"
    ) == "# Modificado externamente\n"

    assert git(
        repo,
        "diff",
        "--cached",
        "--name-only",
    ) == ""
