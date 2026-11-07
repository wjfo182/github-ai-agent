
import pytest

from app.security import (
    validar_tipo_acao,
    validar_acao_executavel,
    validar_geracao_testes,
    validar_conteudo_teste_java,
)


# -----------------------------------------------
# 1. Tipos de ação
# -----------------------------------------------

def test_acao_conhecida_pode_ser_proposta():
    assert validar_tipo_acao("melhorar_readme") is True


@pytest.mark.parametrize(
    "tipo",
    [
        "force_push",
        "executar_shell",
        "excluir_repositorio",
    ],
)
def test_acoes_perigosas_sao_bloqueadas(tipo):
    with pytest.raises(RuntimeError):
        validar_tipo_acao(tipo)


def test_acao_desconhecida_e_bloqueada():
    with pytest.raises(RuntimeError):
        validar_tipo_acao("acao_inventada_pela_ia")


# -----------------------------------------------
# 2. Permissão de execução
# -----------------------------------------------

def test_acao_com_executor_e_permitida():
    assert (
        validar_acao_executavel("melhorar_readme")
        is True
    )


def test_recomendacao_sem_executor_e_bloqueada():
    with pytest.raises(RuntimeError):
        validar_acao_executavel(
            "revisar_visibilidade"
        )


# -----------------------------------------------
# 3. Elegibilidade para testes
# -----------------------------------------------

def criar_analise_testavel():
    return {
        "elegibilidade_testes": {
            "elegivel": True,
            "framework_testes": "JUnit",
            "motivos_bloqueio": [],
        },
        "sugestoes_testes": [
            {
                "classe": "Calculadora",
                "arquivo": (
                    "src/main/java/Calculadora.java"
                ),
                "tipo_teste": "unitario",
                "motivo": "Métodos públicos identificados.",
            }
        ],
    }


def test_bloqueia_projeto_inelegivel():
    analise = criar_analise_testavel()

    analise["elegibilidade_testes"]["elegivel"] = False
    analise["elegibilidade_testes"][
        "motivos_bloqueio"
    ] = ["Framework indisponível."]

    with pytest.raises(RuntimeError):
        validar_geracao_testes(analise)


def test_retorna_candidatos_suportados():
    analise = criar_analise_testavel()

    candidatos = validar_geracao_testes(analise)

    assert isinstance(candidatos, list)
    assert len(candidatos) == 1
    assert candidatos[0]["classe"] == "Calculadora"
    assert candidatos[0]["tipo_teste"] == "unitario"


def test_bloqueia_tipo_de_teste_nao_suportado():
    analise = criar_analise_testavel()

    analise["sugestoes_testes"][0][
        "tipo_teste"
    ] = "controller"

    with pytest.raises(RuntimeError):
        validar_geracao_testes(analise)


# -----------------------------------------------
# 4. Validação de código Java gerado
# -----------------------------------------------

CODIGO_TESTE = """
import org.junit.jupiter.api.Test;

class CalculadoraTest {

    @Test
    void deveSomar() {
        assert 2 + 2 == 4;
    }
}
"""


def test_codigo_java_basico_e_aceito():
    assert validar_conteudo_teste_java(
        CODIGO_TESTE,
        "CalculadoraTest",
        None,
    ) is True


def test_package_incorreto_e_bloqueado():
    codigo = (
        "package com.outro;\n"
        + CODIGO_TESTE
    )

    with pytest.raises(RuntimeError):
        validar_conteudo_teste_java(
            codigo,
            "CalculadoraTest",
            "com.exemplo",
        )


def test_codigo_sem_test_e_bloqueado():
    codigo = CODIGO_TESTE.replace(
        "@Test",
        "",
    )

    with pytest.raises(RuntimeError):
        validar_conteudo_teste_java(
            codigo,
            "CalculadoraTest",
            None,
        )


def test_api_proibida_e_bloqueada():
    codigo = CODIGO_TESTE.replace(
        "assert 2 + 2 == 4;",
        "Runtime.getRuntime().exec(\"comando\");",
    )

    with pytest.raises(RuntimeError):
        validar_conteudo_teste_java(
            codigo,
            "CalculadoraTest",
            None,
        )
