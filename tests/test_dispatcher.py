
from types import SimpleNamespace

import pytest

import app.ai_dispatcher as dispatcher

from app.ai_models import AcaoProposta


REPOSITORIO = "wjfo182/Estudos-Java"


def criar_proposta(tipo="melhorar_readme"):
    return AcaoProposta(
        tipo=tipo,
        prioridade="media",
        titulo="Melhorar documentação",
        motivo="Melhoria identificada na análise.",
    )


def preparar_fluxo(monkeypatch, propostas):
    """
    Simula a seleção do repositório e a resposta
    da IA, sem acessar GitHub ou Ollama.
    """

    analise = {}

    resultado = SimpleNamespace(
        acoes_propostas=propostas
    )
    monkeypatch.setattr(
        dispatcher,
        "exigir_repositorio_autorizado",
        lambda nome: True,
    )

    monkeypatch.setattr(
        dispatcher,
        "selecionar_repositorio",
        lambda: REPOSITORIO,
    )

    monkeypatch.setattr(
        dispatcher,
        "gerar_analise_ia",
        lambda nome: (analise, resultado),
    )

    return analise


# -------------------------------------------------
# 1. Disponibilidade dos executores
# -------------------------------------------------

def test_executor_readme_disponivel():
    assert dispatcher.executor_disponivel(
        "melhorar_readme",
        {},
    ) is True


@pytest.mark.parametrize(
    "tipo",
    [
        "revisar_visibilidade",
        "force_push",
        "acao_inventada",
    ],
)
def test_executor_nao_disponivel(tipo):
    assert dispatcher.executor_disponivel(
        tipo,
        {},
    ) is False


def test_testes_bloqueados_em_projeto_inelegivel():
    analise = {
        "elegibilidade_testes": {
            "elegivel": False,
            "motivos_bloqueio": [
                "Projeto sem framework de testes."
            ],
        }
    }

    assert dispatcher.executor_disponivel(
        "adicionar_testes",
        analise,
    ) is False


# -------------------------------------------------
# 2. Encaminhamento seguro
# -------------------------------------------------

def test_executa_somente_executor_registrado(
    monkeypatch,
):
    chamadas = []

    def executor_falso(nome, analise, proposta):
        chamadas.append(
            (nome, analise, proposta.tipo)
        )

    monkeypatch.setitem(
        dispatcher.EXECUTORES,
        "melhorar_readme",
        executor_falso,
    )

    proposta = criar_proposta()

    dispatcher.executar_acao_proposta(
        REPOSITORIO,
        {},
        proposta,
    )

    assert chamadas == [
        (
            REPOSITORIO,
            {},
            "melhorar_readme",
        )
    ]


def test_force_push_bloqueado_mesmo_com_executor(
    monkeypatch,
):
    chamadas = []

    def executor_falso(*args):
        chamadas.append(args)

    # Simula até mesmo um registro incorreto.
    monkeypatch.setitem(
        dispatcher.EXECUTORES,
        "force_push",
        executor_falso,
    )

    proposta = SimpleNamespace(
        tipo="force_push"
    )

    with pytest.raises(RuntimeError):
        dispatcher.executar_acao_proposta(
            REPOSITORIO,
            {},
            proposta,
        )

    assert chamadas == []


# -------------------------------------------------
# 3. Fluxo interativo
# -------------------------------------------------

def test_cancelamento_nao_executa_acao(
    monkeypatch,
):
    preparar_fluxo(
        monkeypatch,
        [criar_proposta()],
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda mensagem: "0",
    )

    chamadas = []

    monkeypatch.setattr(
        dispatcher,
        "executar_acao_proposta",
        lambda *args: chamadas.append(args),
    )

    dispatcher.executar_fluxo_ia()

    assert chamadas == []


def test_selecao_valida_encaminha_uma_acao(
    monkeypatch,
):
    proposta = criar_proposta()

    preparar_fluxo(
        monkeypatch,
        [proposta],
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda mensagem: "1",
    )

    chamadas = []

    def registrar_execucao(nome, analise, acao):
        chamadas.append(
            (nome, acao.tipo)
        )

    monkeypatch.setattr(
        dispatcher,
        "executar_acao_proposta",
        registrar_execucao,
    )

    dispatcher.executar_fluxo_ia()

    assert chamadas == [
        (
            REPOSITORIO,
            "melhorar_readme",
        )
    ]


def test_recomendacao_sem_executor_nao_executa(
    monkeypatch,
):
    proposta = criar_proposta(
        "revisar_visibilidade"
    )

    preparar_fluxo(
        monkeypatch,
        [proposta],
    )

    def entrada_proibida(mensagem):
        pytest.fail(
            "Não deveria solicitar execução."
        )

    monkeypatch.setattr(
        "builtins.input",
        entrada_proibida,
    )

    chamadas = []

    monkeypatch.setattr(
        dispatcher,
        "executar_acao_proposta",
        lambda *args: chamadas.append(args),
    )

    dispatcher.executar_fluxo_ia()

    assert chamadas == []
