
import pytest

import app.commit_actions as commit_actions


REPOSITORIO = "wjfo182/Estudos-Java"


def preparar_commit_simulado(
    monkeypatch,
    respostas_aprovacao,
):
    """
    Substitui operações reais por simulações.

    Não acessa GitHub, não usa workspace real
    e não cria commits.
    """

    eventos = []
    respostas = iter(respostas_aprovacao)


    monkeypatch.setattr(
        commit_actions,
        "exigir_repositorio_autorizado",
        lambda nome: True,
    )

    monkeypatch.setattr(
        commit_actions,
        "selecionar_repositorio",
        lambda: REPOSITORIO,
    )

    monkeypatch.setattr(
        commit_actions,
        "clonar_repositorio",
        lambda *args: "repositorio-simulado",
    )

    monkeypatch.setattr(
        commit_actions,
        "obter_branch_atual",
        lambda *args: "main",
    )

    monkeypatch.setattr(
        commit_actions,
        "listar_arquivos_stage",
        lambda *args: [],
    )

    monkeypatch.setattr(
        commit_actions,
        "listar_arquivos_para_commit",
        lambda *args: ["README.md"],
    )

    monkeypatch.setattr(
        commit_actions,
        "escolher_arquivos",
        lambda arquivos: ["README.md"],
    )

    monkeypatch.setattr(
        commit_actions,
        "solicitar_aprovacao",
        lambda *args: next(respostas),
    )

    monkeypatch.setattr(
        commit_actions,
        "adicionar_caminho_stage",
        lambda repo, arquivo: eventos.append(
            ("stage", arquivo)
        ),
    )

    monkeypatch.setattr(
        commit_actions,
        "remover_caminho_stage",
        lambda repo, arquivo: eventos.append(
            ("unstage", arquivo)
        ),
    )

    monkeypatch.setattr(
        commit_actions,
        "obter_diff_stage",
        lambda *args: (
            "diff --git a/README.md b/README.md"
        ),
    )

    monkeypatch.setattr(
        commit_actions,
        "criar_commit_local",
        lambda *args: eventos.append(
            ("commit",)
        ),
    )

    monkeypatch.setattr(
        commit_actions,
        "obter_status_git",
        lambda *args: "",
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda *args: "docs: atualiza README",
    )

    monkeypatch.setattr(
        commit_actions,
        "obter_head_commit",
        lambda repo: "head-simulado",
)

    return eventos


# --------------------------------------------
# TESTE 1 - Recusar staging
# --------------------------------------------

def test_recusa_staging_nao_modifica(
    monkeypatch,
):
    eventos = preparar_commit_simulado(
        monkeypatch,
        [False],
    )

    commit_actions.criar_commit_controlado()

    assert eventos == []


# --------------------------------------------
# TESTE 2 - Recusar commit final
# --------------------------------------------

def test_recusa_commit_desfaz_staging(
    monkeypatch,
):
    eventos = preparar_commit_simulado(
        monkeypatch,
        [True, False],
    )

    commit_actions.criar_commit_controlado()

    assert (
        "stage",
        "README.md",
    ) in eventos

    assert (
        "unstage",
        "README.md",
    ) in eventos

    assert (
        "commit",
    ) not in eventos


# --------------------------------------------
# TESTE 3 - Aprovar commit
# --------------------------------------------

def test_aprovacao_cria_um_commit(
    monkeypatch,
):
    eventos = preparar_commit_simulado(
        monkeypatch,
        [True, True],
    )

    commit_actions.criar_commit_controlado()

    assert eventos.count(
        ("stage", "README.md")
    ) == 1

    assert eventos.count(
        ("commit",)
    ) == 1

    assert not any(
        evento[0] == "unstage"
        for evento in eventos
    )


# --------------------------------------------
# TESTE 4 - Selecionar todos os arquivos
# --------------------------------------------

def test_selecionar_todos(
    monkeypatch,
):
    arquivos = [
        "README.md",
        "pom.xml",
    ]

    monkeypatch.setattr(
        "builtins.input",
        lambda *args: "todos",
    )

    selecionados = commit_actions.escolher_arquivos(
        arquivos
    )

    assert selecionados == arquivos


# --------------------------------------------
# TESTE 5 - Seleção sem duplicação
# --------------------------------------------

def test_selecao_nao_duplica_arquivos(
    monkeypatch,
):
    arquivos = [
        "README.md",
        "pom.xml",
    ]

    monkeypatch.setattr(
        "builtins.input",
        lambda *args: "1,2,1",
    )

    selecionados = commit_actions.escolher_arquivos(
        arquivos
    )

    assert selecionados == [
        "README.md",
        "pom.xml",
    ]


# --------------------------------------------
# TESTE 6 - Falha inesperada durante o diff
# --------------------------------------------

def test_falha_no_diff_desfaz_staging(
    monkeypatch,
):
    eventos = preparar_commit_simulado(
        monkeypatch,
        [True, True],
    )

    def simular_falha(*args):
        raise RuntimeError(
            "Falha simulada ao gerar diff"
        )

    monkeypatch.setattr(
        commit_actions,
        "obter_diff_stage",
        simular_falha,
    )

    with pytest.raises(
        RuntimeError,
        match="Falha simulada",
    ):
        commit_actions.criar_commit_controlado()

    assert ("stage", "README.md") in eventos

    assert ("unstage", "README.md") in eventos

    assert ("commit",) not in eventos


# --------------------------------------------
# TESTE 7 - Falha inesperada ao criar commit
# --------------------------------------------

def test_falha_no_commit_desfaz_staging(
    monkeypatch,
):
    eventos = preparar_commit_simulado(
        monkeypatch,
        [True, True],
    )

    def simular_falha(*args):
        raise RuntimeError(
            "Falha simulada ao criar commit"
        )

    monkeypatch.setattr(
        commit_actions,
        "criar_commit_local",
        simular_falha,
    )

    with pytest.raises(
        RuntimeError,
        match="Falha simulada",
    ):
        commit_actions.criar_commit_controlado()

    assert ("stage", "README.md") in eventos

    assert ("unstage", "README.md") in eventos

    assert ("commit",) not in eventos
