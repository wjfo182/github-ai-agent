
from types import SimpleNamespace

import pytest

import app.ai_actions as ai_actions
import app.build_actions as build_actions
import app.structure_actions as structure_actions
import app.test_actions as test_actions


REPOSITORIO = "wjfo182/Estudos-Java"


def proposta(tipo):
    return SimpleNamespace(
        tipo=tipo,
        titulo="Ação simulada",
        motivo="Teste automatizado",
        prioridade="media",
    )


def impedir_clonagem(*args, **kwargs):
    pytest.fail(
        "O executor tentou acessar o repositório "
        "após a recusa de aprovação."
    )


def test_recusa_configurar_build(monkeypatch):
    analise = {
        "branch_analise": "main",
        "java_backend": {
            "java": True,
            "estrutura_java_padrao": True,
        },
        "stack_java": {
            "build_tool": None,
        },
    }

    monkeypatch.setattr(
        build_actions,
        "escolher_java_release",
        lambda: "25",
    )

    monkeypatch.setattr(
        build_actions,
        "solicitar_aprovacao",
        lambda *args: False,
    )

    monkeypatch.setattr(
        build_actions,
        "clonar_repositorio",
        impedir_clonagem,
    )

    build_actions.executar_configurar_build(
        REPOSITORIO,
        analise,
        proposta("configurar_build"),
    )


def test_recusa_organizar_estrutura(monkeypatch):
    analise = {
        "branch_analise": "main",
    }

    movimentos = [
        {
            "origem": "src/Main.java",
            "destino": "src/main/java/Main.java",
        }
    ]

    monkeypatch.setattr(
        structure_actions,
        "validar_organizacao_estrutura",
        lambda analise: movimentos,
    )

    monkeypatch.setattr(
        structure_actions,
        "solicitar_aprovacao",
        lambda *args: False,
    )

    monkeypatch.setattr(
        structure_actions,
        "clonar_repositorio",
        impedir_clonagem,
    )

    structure_actions.executar_organizar_estrutura(
        REPOSITORIO,
        analise,
        proposta("organizar_estrutura"),
    )


def test_recusa_adicionar_testes(monkeypatch):
    analise = {
        "elegibilidade_testes": {
            "framework_testes": "JUnit",
        },
        "estrutura_codigo_java": [
            {
                "arquivo": (
                    "src/main/java/Calculadora.java"
                ),
                "classe": "Calculadora",
                "package": None,
            }
        ],
        "branch_analise": "main",
    }

    candidatos = [
        {
            "classe": "Calculadora",
            "arquivo": (
                "src/main/java/Calculadora.java"
            ),
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

    monkeypatch.setattr(
        test_actions,
        "solicitar_aprovacao",
        lambda *args: False,
    )

    monkeypatch.setattr(
        test_actions,
        "clonar_repositorio",
        impedir_clonagem,
    )

    test_actions.executar_adicionar_testes(
        REPOSITORIO,
        analise,
        proposta("adicionar_testes"),
    )


def test_recusa_melhorar_readme(monkeypatch):
    analise = {
        "branch_analise": "main",
        "analise_branches": {
            "branches": {
                "main": {
                    "arquivos": [
                        "README.md"
                    ],
                }
            }
        },
    }

    monkeypatch.setattr(
        ai_actions,
        "solicitar_aprovacao",
        lambda *args: False,
    )

    monkeypatch.setattr(
        ai_actions,
        "clonar_repositorio",
        impedir_clonagem,
    )

    ai_actions.executar_melhorar_readme(
        REPOSITORIO,
        analise,
        proposta("melhorar_readme"),
    )
