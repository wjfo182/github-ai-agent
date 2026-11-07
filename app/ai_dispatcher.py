from app.ai_actions import (
    executar_melhorar_readme,
)

from app.ai_agent import (
    gerar_analise_ia,
)

from app.repository_selector import (
    selecionar_repositorio,
)

from app.security import (
    ACOES_EXECUTAVEIS,
    validar_acao_executavel,
    validar_acao_no_contexto,
)

from app.test_actions import (
    executar_adicionar_testes,
)
from app.build_actions import (
    executar_configurar_build,
)

from app.structure_actions import (
    executar_organizar_estrutura,
)

# Registro explícito.
#
# Nunca use eval(), exec(), getattr() baseado
# diretamente em texto produzido pela IA.
EXECUTORES = {
    "melhorar_readme": executar_melhorar_readme,
    "adicionar_testes": executar_adicionar_testes,
    "configurar_build": executar_configurar_build,
    "organizar_estrutura": executar_organizar_estrutura,
}

def executor_disponivel(
    tipo,
    analise,
):
    """
    Verifica se existe executor e se a ação
    é permitida no contexto deste repositório.
    """

    if (
        tipo not in ACOES_EXECUTAVEIS
        or tipo not in EXECUTORES
    ):
        return False

    try:
        validar_acao_no_contexto(
            tipo,
            analise,
        )

    except RuntimeError:
        return False

    return True

def executar_acao_proposta(
    nome_completo,
    analise,
    proposta,
):
    """
    Encaminha uma ação validada para um executor
    registrado explicitamente.
    """

    validar_acao_executavel(
        proposta.tipo
    )

    validar_acao_no_contexto(
        proposta.tipo,
        analise,
)

    executor = EXECUTORES.get(
        proposta.tipo
    )

    if executor is None:
        raise RuntimeError(
            f"Não existe executor registrado "
            f"para '{proposta.tipo}'."
        )

    return executor(
        nome_completo,
        analise,
        proposta,
    )


def executar_fluxo_ia():
    """
    Analisa um repositório e permite ao usuário
    escolher UMA ação executável proposta pela IA.
    """

    nome_completo = selecionar_repositorio()

    print(
        f"\nAnalisando {nome_completo} com IA..."
    )

    analise, resultado = gerar_analise_ia(
        nome_completo
    )

    propostas = resultado.acoes_propostas

    if not propostas:
        print(
            "\nA IA não propôs nenhuma ação."
        )
        return

    print("\n" + "=" * 60)
    print("AÇÕES PROPOSTAS PELA IA")
    print("=" * 60)

    executaveis = {}

    for indice, proposta in enumerate(
        propostas,
        start=1,
    ):
        disponivel = executor_disponivel(
            proposta.tipo, 
            analise
        )

        status = (
            "EXECUTÁVEL"
            if disponivel
            else "SOMENTE RECOMENDAÇÃO"
        )

        print(
            f"\n{indice}. "
            f"[{proposta.prioridade.upper()}] "
            f"{proposta.titulo}"
        )

        print(
            f"   Tipo: {proposta.tipo}"
        )

        print(
            f"   Status: {status}"
        )

        print(
            f"   Motivo: {proposta.motivo}"
        )

        if disponivel:
            executaveis[
                str(indice)
            ] = proposta

    if not executaveis:
        print(
            "\nNenhuma das ações propostas possui "
            "executor seguro implementado."
        )
        return

    print(
        "\n0. Não executar nenhuma ação"
    )

    escolha = input(
        "\nEscolha uma ação executável: "
    ).strip()

    if escolha == "0":
        print(
            "\nNenhuma ação selecionada."
        )
        return

    proposta = executaveis.get(
        escolha
    )

    if proposta is None:
        print(
            "\nOpção inválida ou ação "
            "ainda não executável."
        )
        return

    print(
        f"\nAção selecionada: "
        f"{proposta.titulo}"
    )

    executar_acao_proposta(
        nome_completo,
        analise,
        proposta,
    )

def main():
    try:
        executar_fluxo_ia()

    except (
        RuntimeError,
        ValueError,
    ) as erro:
        print(
            f"\nA operação foi interrompida: {erro}"
        )


if __name__ == "__main__":
    main()