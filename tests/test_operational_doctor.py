
import subprocess

from types import SimpleNamespace

import pytest

from app.operational_doctor import verificar_servicos


def consultar(executor, executaveis=None):
    if executaveis is None:
        executaveis = {"gh", "ollama"}

    return verificar_servicos(
        localizar_executavel=(
            lambda nome: (
                f"simulado/{nome}"
                if nome in executaveis
                else None
            )
        ),
        executar_comando=executor,
    )


def executar_simulado_ok(comando, **kwargs):
    return SimpleNamespace(returncode=0)


def obter(resultados, nome):
    return next(
        item
        for item in resultados
        if item.nome == nome
    )


# TESTE 1: serviços respondendo

def test_servicos_operacionais():
    resultados = consultar(executar_simulado_ok)

    assert len(resultados) == 2

    assert all(
        item.status == "OK"
        for item in resultados
    )


# TESTE 2: falha na autenticação GitHub

def test_github_sem_autenticacao():

    def executar(comando, **kwargs):
        codigo = 1 if comando[0] == "gh" else 0
        return SimpleNamespace(returncode=codigo)

    resultados = consultar(executar)

    assert obter(
        resultados,
        "GitHub: autenticação",
    ).status == "FALHA"


# TESTE 3: serviço Ollama indisponível

def test_ollama_indisponivel():

    def executar(comando, **kwargs):
        codigo = 1 if comando[0] == "ollama" else 0
        return SimpleNamespace(returncode=codigo)

    resultados = consultar(executar)

    assert obter(
        resultados,
        "Ollama: serviço",
    ).status == "FALHA"


# TESTE 4: executável ausente

def test_executavel_ausente_nao_e_executado():
    chamadas = []

    def executar(comando, **kwargs):
        chamadas.append(comando)
        return SimpleNamespace(returncode=0)

    resultados = consultar(
        executar,
        executaveis={"ollama"},
    )

    assert obter(
        resultados,
        "GitHub: autenticação",
    ).status == "FALHA"

    assert len(chamadas) == 1
    assert chamadas[0] == ["ollama", "list"]


# TESTE 5: comando excede tempo limite

def test_comando_com_timeout():

    def executar(comando, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd=comando,
            timeout=kwargs["timeout"],
        )

    resultados = consultar(executar)

    assert all(
        item.status == "FALHA"
        for item in resultados
    )


# TESTE 6: falha ao iniciar comando

def test_falha_no_sistema_operacional():

    def executar(comando, **kwargs):
        raise OSError("Falha simulada")

    resultados = consultar(executar)

    assert all(
        item.status == "FALHA"
        for item in resultados
    )


# TESTE 7: comandos restritos e não interativos

def test_apenas_comandos_de_consulta():
    chamadas = []

    def executar(comando, **kwargs):
        chamadas.append((comando, kwargs))
        return SimpleNamespace(returncode=0)

    consultar(executar)

    assert [item[0] for item in chamadas] == [
        [
            "gh", "auth", "status",
            "--hostname", "github.com",
        ],
        [
            "ollama", "list",
        ],
    ]

    for comando, opcoes in chamadas:
        assert opcoes["timeout"] == 10
        assert opcoes["check"] is False
        assert opcoes["stdin"] == subprocess.DEVNULL
        assert opcoes["stdout"] == subprocess.DEVNULL
        assert opcoes["stderr"] == subprocess.DEVNULL
