
from types import SimpleNamespace

import pytest

import app.ai_actions as ai_actions
import app.test_actions as test_actions


REPOSITORIO = "wjfo182/Estudos-Java"


def proposta(tipo):
    return SimpleNamespace(
        tipo=tipo,
        prioridade="media",
        titulo="Ação de teste",
        motivo="Verificação automatizada de segurança.",
    )


def impedir_escrita(*args, **kwargs):
    pytest.fail(
        "O executor tentou gravar um arquivo sem autorização."
    )


def preparar_git_simulado(monkeypatch, modulo, raiz):
    """
    Substitui operações Git por funções simuladas.
    Não acessa o GitHub e não executa comandos Git.
    """

    monkeypatch.setattr(
        modulo,
        "clonar_repositorio",
        lambda nome: str(raiz),
    )

    monkeypatch.setattr(
        modulo,
        "repositorio_esta_limpo",
        lambda repo: True,
    )

    monkeypatch.setattr(
        modulo,
        "atualizar_todas_referencias",
        lambda repo: None,
    )

    monkeypatch.setattr(
        modulo,
        "selecionar_branch",
        lambda repo, branch: None,
    )

    monkeypatch.setattr(
        modulo,
        "atualizar_branch_local_ff",
        lambda repo, branch: None,
    )

    monkeypatch.setattr(
        modulo,
        "escrever_arquivo_local",
        impedir_escrita,
    )


def preparar_analise_testes():
    return {
        "branch_analise": "main",
        "elegibilidade_testes": {
            "framework_testes": "JUnit",
        },
        "estrutura_codigo_java": [
            {
                "arquivo": "src/main/java/Calculadora.java",
                "classe": "Calculadora",
                "package": None,
            }
        ],
    }


def preparar_executor_testes(monkeypatch, raiz):
    preparar_git_simulado(
        monkeypatch,
        test_actions,
        raiz,
    )

    candidatos = [
        {
            "classe": "Calculadora",
            "arquivo": "src/main/java/Calculadora.java",
            "tipo_teste": "unitario",
            "motivo": "Métodos públicos disponíveis.",
        }
    ]

    monkeypatch.setattr(
        test_actions,
        "validar_geracao_testes",
        lambda analise: candidatos,
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda mensagem: "1",
    )


def criar_fonte_java(raiz):
    origem = raiz / "src/main/java/Calculadora.java"

    origem.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    origem.write_text(
        "public class Calculadora { "
        "public int somar(int a, int b) { "
        "return a + b; "
        "} }",
        encoding="utf-8",
    )

    return origem


# -------------------------------------------------
# 1. Recusa na aprovação final do README
# -------------------------------------------------

def test_recusa_final_readme_nao_grava(
    monkeypatch,
    tmp_path,
):
    readme = tmp_path / "README.md"

    conteudo_original = "# README original\n"

    readme.write_text(
        conteudo_original,
        encoding="utf-8",
    )

    preparar_git_simulado(
        monkeypatch,
        ai_actions,
        tmp_path,
    )

    respostas = iter([True, False])

    monkeypatch.setattr(
        ai_actions,
        "solicitar_aprovacao",
        lambda *args: next(respostas),
    )

    monkeypatch.setattr(
        ai_actions,
        "consultar_ia_estruturada",
        lambda *args: SimpleNamespace(
            conteudo_markdown=(
                "# README melhorado\n\n"
                "Documentação atualizada para estudos Java.\n"
            ),
            alteracoes_principais=[
                "Melhoria da documentação"
            ],
            justificativa=(
                "Organização das informações do projeto."
            ),
        ),
    )

    analise = {
        "branch_analise": "main",
        "analise_branches": {
            "branches": {
                "main": {
                    "arquivos": ["README.md"],
                }
            }
        },
    }

    ai_actions.executar_melhorar_readme(
        REPOSITORIO,
        analise,
        proposta("melhorar_readme"),
    )

    assert readme.read_text(
        encoding="utf-8"
    ) == conteudo_original


# -------------------------------------------------
# 2. Recusa na aprovação final do teste Java
# -------------------------------------------------

def test_recusa_final_teste_nao_cria(
    monkeypatch,
    tmp_path,
):
    criar_fonte_java(tmp_path)

    preparar_executor_testes(
        monkeypatch,
        tmp_path,
    )

    respostas = iter([True, False])

    monkeypatch.setattr(
        test_actions,
        "solicitar_aprovacao",
        lambda *args: next(respostas),
    )

    codigo_teste = """
import org.junit.jupiter.api.Test;

class CalculadoraTest {

    @Test
    void deveSomar() {
        assert 2 + 2 == 4;
    }
}
"""

    monkeypatch.setattr(
        test_actions,
        "consultar_ia_estruturada",
        lambda *args: SimpleNamespace(
            conteudo_java=codigo_teste,
            metodos_testados=["somar"],
            justificativa="Verificação da soma.",
        ),
    )

    test_actions.executar_adicionar_testes(
        REPOSITORIO,
        preparar_analise_testes(),
        proposta("adicionar_testes"),
    )

    destino = (
        tmp_path
        / "src/test/java/CalculadoraTest.java"
    )

    assert not destino.exists()


# -------------------------------------------------
# 3. Não sobrescrever teste existente
# -------------------------------------------------

def test_bloqueia_teste_ja_existente(
    monkeypatch,
    tmp_path,
):
    criar_fonte_java(tmp_path)

    destino = (
        tmp_path
        / "src/test/java/CalculadoraTest.java"
    )

    destino.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    destino.write_text(
        "// Teste existente",
        encoding="utf-8",
    )

    preparar_executor_testes(
        monkeypatch,
        tmp_path,
    )

    monkeypatch.setattr(
        test_actions,
        "solicitar_aprovacao",
        lambda *args: True,
    )

    monkeypatch.setattr(
        test_actions,
        "consultar_ia_estruturada",
        lambda *args: pytest.fail(
            "A IA não deveria ser consultada."
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="já existe",
    ):
        test_actions.executar_adicionar_testes(
            REPOSITORIO,
            preparar_analise_testes(),
            proposta("adicionar_testes"),
        )

    assert destino.read_text(
        encoding="utf-8"
    ) == "// Teste existente"


# -------------------------------------------------
# 4. Bloquear repositório com alterações locais
# -------------------------------------------------

def test_bloqueia_repositorio_sujo(
    monkeypatch,
    tmp_path,
):
    criar_fonte_java(tmp_path)

    preparar_executor_testes(
        monkeypatch,
        tmp_path,
    )

    monkeypatch.setattr(
        test_actions,
        "solicitar_aprovacao",
        lambda *args: True,
    )

    monkeypatch.setattr(
        test_actions,
        "repositorio_esta_limpo",
        lambda repo: False,
    )

    monkeypatch.setattr(
        test_actions,
        "consultar_ia_estruturada",
        lambda *args: pytest.fail(
            "A IA não deveria ser consultada."
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="alterações locais",
    ):
        test_actions.executar_adicionar_testes(
            REPOSITORIO,
            preparar_analise_testes(),
            proposta("adicionar_testes"),
        )
