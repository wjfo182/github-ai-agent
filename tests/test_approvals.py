
import pytest

from app.approvals import solicitar_aprovacao


@pytest.mark.parametrize(
    "resposta",
    ["s", "sim"],
)
def test_aprovacao_positiva(monkeypatch, resposta):
    monkeypatch.setattr(
        "builtins.input",
        lambda mensagem: resposta,
    )

    resultado = solicitar_aprovacao(
        "Teste de aprovação",
        ["Operação simulada"],
    )

    assert resultado is True


@pytest.mark.parametrize(
    "resposta",
    ["n", "nao", "não"],
)
def test_aprovacao_negativa(monkeypatch, resposta):
    monkeypatch.setattr(
        "builtins.input",
        lambda mensagem: resposta,
    )

    resultado = solicitar_aprovacao(
        "Teste de recusa",
        ["Nenhuma alteração permitida"],
    )

    assert resultado is False


def test_resposta_invalida_seguida_de_recusa(
    monkeypatch,
):
    respostas = iter(
        ["talvez", "n"]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda mensagem: next(respostas),
    )

    resultado = solicitar_aprovacao(
        "Teste de entrada inválida",
        ["Operação simulada"],
    )

    assert resultado is False
