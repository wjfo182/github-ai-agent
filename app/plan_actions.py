
from app.ai_dispatcher import (
    executor_disponivel,
    executar_acao_proposta,
)

from app.ai_models import AcaoProposta

from app.approvals import solicitar_aprovacao

from app.planner import gerar_plano_portfolio

from app.repository import analisar_portfolio_repositorio

from app.repository_selector import selecionar_repositorio


def obter_plano(nome_completo):
    """
    Obtém a análise e gera um plano determinístico.

    Não executa alterações.
    """

    analise = analisar_portfolio_repositorio(
        nome_completo
    )

    plano = gerar_plano_portfolio(analise)

    return analise, plano


def mostrar_etapas(plano, analise):
    """
    Mostra todas as etapas e identifica quais
    possuem executor disponível no contexto.
    """

    executaveis = {}

    print("\n" + "=" * 60)
    print("PLANO DE EVOLUÇÃO")
    print("=" * 60)

    for indice, etapa in enumerate(plano, start=1):

        disponivel = executor_disponivel(
            etapa["tipo"],
            analise,
        )

        status = (
            "EXECUTÁVEL"
            if disponivel
            else "SOMENTE RECOMENDAÇÃO"
        )

        print(
            f"\n{indice}. "
            f"[{etapa['prioridade'].upper()}] "
            f"{etapa['titulo']}"
        )

        print(f"   Tipo: {etapa['tipo']}")
        print(f"   Status: {status}")
        print(f"   Motivo: {etapa['motivo']}")

        if disponivel:
            executaveis[str(indice)] = etapa

    return executaveis


def exibir_plano_portfolio():
    """
    Exibe o plano, sem executar ações.
    """

    nome = selecionar_repositorio()

    analise, plano = obter_plano(nome)

    if not plano:
        print("\nNenhuma melhoria prioritária identificada.")
        return

    mostrar_etapas(plano, analise)

    print("\nNenhuma alteração foi realizada.")


def executar_etapa_plano():
    """
    Permite executar uma única etapa do plano,
    sempre por meio do dispatcher e das aprovações.
    """

    nome = selecionar_repositorio()

    analise, plano = obter_plano(nome)

    if not plano:
        print("\nNenhuma melhoria prioritária identificada.")
        return

    executaveis = mostrar_etapas(plano, analise)

    if not executaveis:
        print("\nNenhuma etapa possui executor disponível.")
        return

    print("\n0. Cancelar")

    escolha = input(
        "\nEscolha uma etapa executável: "
    ).strip()

    if escolha == "0":
        print("\nOperação cancelada.")
        return

    etapa = executaveis.get(escolha)

    if etapa is None:
        print("\nEtapa inválida ou não executável.")
        return

    # Reconsulta o GitHub antes da execução,
    # evitando usar um plano remoto desatualizado.
    analise_atual, plano_atual = obter_plano(nome)

    continua_necessaria = any(
        item["tipo"] == etapa["tipo"]
        for item in plano_atual
    )

    if not continua_necessaria:
        raise RuntimeError(
            "A etapa não faz mais parte do plano atualizado."
        )

    if not executor_disponivel(
        etapa["tipo"],
        analise_atual,
    ):
        raise RuntimeError(
            "A ação deixou de ser executável "
            "no contexto atual."
        )

    # Constrói uma proposta com o mesmo contrato
    # validado no fluxo da IA.
    proposta = AcaoProposta(
        tipo=etapa["tipo"],
        prioridade=etapa["prioridade"],
        titulo=etapa["titulo"],
        motivo=etapa["motivo"],
    )

    aprovado = solicitar_aprovacao(
        "Encaminhar etapa do plano",
        [
            f"Repositório: {nome}",
            f"Ação: {proposta.tipo}",
            f"Objetivo: {proposta.titulo}",
            "Executar apenas esta etapa.",
            "O executor poderá solicitar novas aprovações.",
            "Não fazer commit automático.",
            "Não fazer push automático.",
        ],
    )

    if not aprovado:
        print("\nEtapa cancelada.")
        return

    # Somente o dispatcher pode selecionar
    # o executor Python registrado.
    executar_acao_proposta(
        nome,
        analise_atual,
        proposta,
    )

    print(
        "\nFluxo da etapa encerrado. "
        "Se houve alterações locais, revise-as "
        "antes de criar um commit."
    )

    print(
        "Recalcule o plano após publicar "
        "as alterações no GitHub."
    )


def main():
    try:
        exibir_plano_portfolio()

    except (RuntimeError, ValueError) as erro:
        print(f"\nOperação interrompida: {erro}")


if __name__ == "__main__":
    main()
