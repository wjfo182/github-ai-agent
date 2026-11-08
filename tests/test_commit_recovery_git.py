
import shutil
import subprocess

import pytest

import app.commit_actions as commit_actions


pytestmark = pytest.mark.skipif(
    shutil.which("git") is None,
    reason="Git não encontrado.",
)


def git(repo, *argumentos):
    """Executa Git apenas no repositório de teste."""

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
    """Cria um Git local, sem remoto."""

    git(tmp_path, "init", "-b", "main")

    git(
        tmp_path, "config",
        "user.name", "Teste Local",
    )

    git(
        tmp_path, "config",
        "user.email", "teste@example.invalid",
    )

    readme = tmp_path / "README.md"

    readme.write_text(
        "# Projeto original\n",
        encoding="utf-8",
    )

    git(tmp_path, "add", "--", "README.md")
    git(tmp_path, "commit", "-m", "commit inicial")

    # Alteração local ainda não preparada.
    readme.write_text(
        "# Projeto atualizado\n",
        encoding="utf-8",
    )

    assert git(tmp_path, "remote") == ""

    return tmp_path


def preparar_fluxo_real(monkeypatch, repo):
    """
    Executa comandos Git reais no tmp_path.

    Simula apenas a interface, seleção e
    aprovações do usuário.
    """
    monkeypatch.setattr(
        commit_actions,
        "exigir_repositorio_autorizado",
        lambda nome: True,
    )

    monkeypatch.setattr(
        commit_actions,
        "selecionar_repositorio",
        lambda: "teste-local/projeto",
    )

    monkeypatch.setattr(
        commit_actions,
        "clonar_repositorio",
        lambda nome: repo,
    )

    monkeypatch.setattr(
        commit_actions,
        "obter_branch_atual",
        lambda r: git(r, "branch", "--show-current"),
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
        lambda r: ["README.md"],
    )

    monkeypatch.setattr(
        commit_actions,
        "escolher_arquivos",
        lambda arquivos: ["README.md"],
    )

    monkeypatch.setattr(
        commit_actions,
        "solicitar_aprovacao",
        lambda *args, **kwargs: True,
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
        "criar_commit_local",
        lambda r, mensagem: git(
            r, "commit", "-m", mensagem
        ),
    )

    monkeypatch.setattr(
        commit_actions,
        "obter_status_git",
        lambda r: git(r, "status", "--short"),
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda mensagem: "docs: atualiza README",
    )


def verificar_alteracoes_preservadas(repo):
    """Confirma que nada foi perdido ou staged."""

    assert git(
        repo, "diff", "--cached", "--name-only"
    ) == ""

    assert "README.md" in git(
        repo, "diff", "--name-only"
    ).splitlines()

    assert (repo / "README.md").read_text(
        encoding="utf-8"
    ) == "# Projeto atualizado\n"


# TESTE 1: falha ao gerar diff

def test_falha_diff_limpa_staging(
    monkeypatch, repo_temporario
):
    repo = repo_temporario

    preparar_fluxo_real(monkeypatch, repo)

    head_inicial = git(repo, "rev-parse", "HEAD")

    def falhar(*args):
        raise RuntimeError("Falha simulada no diff")

    monkeypatch.setattr(
        commit_actions, "obter_diff_stage", falhar
    )

    with pytest.raises(
        RuntimeError, match="Falha simulada"
    ):
        commit_actions.criar_commit_controlado()

    assert git(repo, "rev-parse", "HEAD") == head_inicial

    verificar_alteracoes_preservadas(repo)


# TESTE 2: falha antes de criar commit

def test_falha_commit_preserva_arquivos(
    monkeypatch, repo_temporario
):
    repo = repo_temporario

    preparar_fluxo_real(monkeypatch, repo)

    head_inicial = git(repo, "rev-parse", "HEAD")

    def falhar(*args):
        raise RuntimeError("Falha simulada no commit")

    monkeypatch.setattr(
        commit_actions, "criar_commit_local", falhar
    )

    with pytest.raises(
        RuntimeError, match="Falha simulada"
    ):
        commit_actions.criar_commit_controlado()

    assert git(repo, "rev-parse", "HEAD") == head_inicial

    verificar_alteracoes_preservadas(repo)


# TESTE 3: fluxo normal de commit

def test_commit_real_concluido(
    monkeypatch, repo_temporario
):
    repo = repo_temporario

    preparar_fluxo_real(monkeypatch, repo)

    head_inicial = git(repo, "rev-parse", "HEAD")

    commit_actions.criar_commit_controlado()

    assert git(repo, "rev-parse", "HEAD") != head_inicial

    assert git(
        repo, "log", "-1", "--format=%s"
    ) == "docs: atualiza README"

    assert git(repo, "status", "--porcelain") == ""

    assert git(repo, "remote") == ""


# TESTE 4: erro após commit confirmado

def test_erro_apos_commit_preserva_commit(
    monkeypatch, repo_temporario
):
    repo = repo_temporario

    preparar_fluxo_real(monkeypatch, repo)

    head_inicial = git(repo, "rev-parse", "HEAD")

    def falhar_status(*args):
        raise RuntimeError(
            "Falha simulada ao consultar status"
        )

    monkeypatch.setattr(
        commit_actions,
        "obter_status_git",
        falhar_status,
    )

    with pytest.raises(
        RuntimeError, match="Falha simulada"
    ):
        commit_actions.criar_commit_controlado()

    assert git(repo, "rev-parse", "HEAD") != head_inicial

    assert git(
        repo, "log", "-1", "--format=%s"
    ) == "docs: atualiza README"

    assert git(repo, "status", "--porcelain") == ""

# -------------------------------------------------
# TESTE 5
# Commit realizado, mas Python recebe uma exceção
# -------------------------------------------------

def test_commit_criado_mas_retorno_falhou(
    monkeypatch,
    repo_temporario,
):
    repo = repo_temporario

    preparar_fluxo_real(
        monkeypatch,
        repo,
    )

    head_inicial = git(
        repo,
        "rev-parse",
        "HEAD",
    )

    def criar_commit_e_falhar(
        diretorio,
        mensagem,
    ):
        # O Git cria efetivamente o commit.
        git(
            diretorio,
            "commit",
            "-m",
            mensagem,
        )

        # Simula falha posterior ao sucesso.
        raise RuntimeError(
            "Erro após criação do commit"
        )

    monkeypatch.setattr(
        commit_actions,
        "criar_commit_local",
        criar_commit_e_falhar,
    )

    with pytest.raises(
        RuntimeError,
        match="Erro após criação",
    ):
        commit_actions.criar_commit_controlado()

    # O commit deve continuar existindo.
    assert git(
        repo,
        "rev-parse",
        "HEAD",
    ) != head_inicial

    assert git(
        repo,
        "log",
        "-1",
        "--format=%s",
    ) == "docs: atualiza README"

    assert git(
        repo,
        "status",
        "--porcelain",
    ) == ""


# -------------------------------------------------
# TESTE 6
# Staging modificado após aprovação do diff
# -------------------------------------------------

def test_staging_alterado_bloqueia_commit(
    monkeypatch,
    repo_temporario,
):
    repo = repo_temporario

    preparar_fluxo_real(
        monkeypatch,
        repo,
    )

    head_inicial = git(
        repo,
        "rev-parse",
        "HEAD",
    )

    obter_diff_original = (
        commit_actions.obter_diff_stage
    )

    chamadas = 0

    def obter_diff_com_alteracao(diretorio):
        nonlocal chamadas

        chamadas += 1

        if chamadas == 2:

            # Simula outro processo adicionando
            # um arquivo ao staging.
            arquivo = (
                diretorio / "externo.txt"
            )

            arquivo.write_text(
                "Alteração externa\n",
                encoding="utf-8",
            )

            git(
                diretorio,
                "add",
                "--",
                "externo.txt",
            )

        return obter_diff_original(
            diretorio
        )

    monkeypatch.setattr(
        commit_actions,
        "obter_diff_stage",
        obter_diff_com_alteracao,
    )

    with pytest.raises(
        RuntimeError,
        match="staging mudou",
    ):
        commit_actions.criar_commit_controlado()

    # Nenhum commit novo.
    assert git(
        repo,
        "rev-parse",
        "HEAD",
    ) == head_inicial

    # O agente não deve apagar o staging
    # modificado por outro processo.
    arquivos_stage = git(
        repo,
        "diff",
        "--cached",
        "--name-only",
    ).splitlines()

    assert "README.md" in arquivos_stage
    assert "externo.txt" in arquivos_stage
