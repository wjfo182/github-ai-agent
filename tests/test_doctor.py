
import json

import pytest

from app.doctor import (
    ARQUIVOS_ESSENCIAIS,
    verificar_prontidao,
)


@pytest.fixture
def projeto(tmp_path):
    """
    Monta um projeto fictício para os testes.

    Não acessa o agente real.
    """

    for caminho in ARQUIVOS_ESSENCIAIS:
        arquivo = tmp_path / caminho

        arquivo.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        arquivo.write_text(
            "# arquivo de teste\n",
            encoding="utf-8",
        )

    configuracao = (
        tmp_path
        / "config"
        / "authorized_repositories.json"
    )

    configuracao.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    configuracao.write_text(
        json.dumps({"repositorios": []}),
        encoding="utf-8",
    )

    (tmp_path / "workspace").mkdir()
    (tmp_path / "tests").mkdir()

    return tmp_path


def diagnosticar(
    projeto,
    *,
    executaveis=None,
    modulos=None,
):
    if executaveis is None:
        executaveis = {"git", "gh", "ollama"}

    if modulos is None:
        modulos = {"pydantic", "ollama", "pytest"}

    return verificar_prontidao(
        projeto,
        localizar_executavel=(
            lambda nome: (
                f"simulado/{nome}"
                if nome in executaveis
                else None
            )
        ),
        localizar_modulo=(
            lambda nome: (
                object()
                if nome in modulos
                else None
            )
        ),
    )


def obter_item(resultados, nome):
    return next(
        item
        for item in resultados
        if item.nome == nome
    )


# TESTE 1 - Ambiente completo

def test_ambiente_completo(projeto):
    resultados = diagnosticar(projeto)

    assert all(
        item.status == "OK"
        for item in resultados
    )


# TESTES 2, 3 e 4 - Executáveis ausentes

@pytest.mark.parametrize(
    "comando",
    ["git", "gh", "ollama"],
)
def test_executavel_ausente(
    projeto,
    comando,
):
    executaveis = {
        "git", "gh", "ollama"
    } - {comando}

    resultados = diagnosticar(
        projeto,
        executaveis=executaveis,
    )

    assert obter_item(
        resultados, comando
    ).status == "FALHA"


# TESTES 5 e 6 - Módulos essenciais ausentes

@pytest.mark.parametrize(
    "modulo",
    ["pydantic", "ollama"],
)
def test_modulo_essencial_ausente(
    projeto,
    modulo,
):
    modulos = {
        "pydantic", "ollama", "pytest"
    } - {modulo}

    resultados = diagnosticar(
        projeto,
        modulos=modulos,
    )

    assert obter_item(
        resultados,
        f"Python: {modulo}",
    ).status == "FALHA"


# TESTE 7 - Configuração ausente

def test_configuracao_ausente(projeto):
    arquivo = (
        projeto
        / "config"
        / "authorized_repositories.json"
    )

    arquivo.unlink()

    resultados = diagnosticar(projeto)

    assert obter_item(
        resultados,
        "Configuração de permissões",
    ).status == "FALHA"


# TESTE 8 - JSON inválido

def test_configuracao_invalida(projeto):
    arquivo = (
        projeto
        / "config"
        / "authorized_repositories.json"
    )

    arquivo.write_text(
        "{json inválido",
        encoding="utf-8",
    )

    resultados = diagnosticar(projeto)

    assert obter_item(
        resultados,
        "Configuração de permissões",
    ).status == "FALHA"


# TESTE 9 - Arquivo essencial ausente

def test_codigo_essencial_ausente(projeto):
    (projeto / "app/security.py").unlink()

    resultados = diagnosticar(projeto)

    assert obter_item(
        resultados,
        "app/security.py",
    ).status == "FALHA"


# TESTE 10 - pytest é opcional no runtime

def test_pytest_ausente_gera_aviso(projeto):
    resultados = diagnosticar(
        projeto,
        modulos={"pydantic", "ollama"},
    )

    assert obter_item(
        resultados,
        "Python: pytest",
    ).status == "AVISO"


# TESTE 11 - Workspace ausente gera aviso

def test_workspace_ausente_gera_aviso(projeto):
    (projeto / "workspace").rmdir()

    resultados = diagnosticar(projeto)

    assert obter_item(
        resultados,
        "Pasta: workspace",
    ).status == "AVISO"


# TESTE 12 - Diagnóstico não altera configuração

def test_diagnostico_nao_altera_configuracao(
    projeto,
):
    arquivo = (
        projeto
        / "config"
        / "authorized_repositories.json"
    )

    antes = arquivo.read_bytes()

    diagnosticar(projeto)

    depois = arquivo.read_bytes()

    assert antes == depois
