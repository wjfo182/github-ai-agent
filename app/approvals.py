def solicitar_aprovacao(titulo, detalhes):
    """
    Solicita confirmação explícita do usuário
    antes de executar uma alteração.
    """

    print("\n" + "=" * 60)
    print("APROVAÇÃO NECESSÁRIA")
    print("=" * 60)

    print(f"\nAção proposta: {titulo}")

    print("\nO agente pretende:")

    if isinstance(detalhes, str):
        detalhes = [detalhes]

    for detalhe in detalhes:
        print(f"  - {detalhe}")

    print("\nNenhuma alteração será executada sem aprovação.")

    while True:
        resposta = input(
            "\nDeseja autorizar esta ação? [s/n]: "
        ).strip().lower()

        if resposta in {"s", "sim"}:
            print("\nAção aprovada.")
            return True

        if resposta in {"n", "nao", "não"}:
            print("\nAção cancelada.")
            return False

        print(
            "Resposta inválida. Digite 's' para sim "
            "ou 'n' para não."
        )