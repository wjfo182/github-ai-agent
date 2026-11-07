from app.permissions import (
    carregar_autorizados,
    revogar_repositorio,
)

from app.approvals import solicitar_aprovacao


def listar_repositorios_autorizados():
    """
    Exibe os repositórios autorizados para alterações.
    """

    repositorios = carregar_autorizados()

    print("\n" + "=" * 60)
    print("REPOSITÓRIOS AUTORIZADOS")
    print("=" * 60)

    if not repositorios:
        print("\nNenhum repositório autorizado.")
        return

    for indice, repositorio in enumerate(
        repositorios,
        start=1,
    ):
        print(
            f"{indice}. {repositorio}"
        )


def revogar_autorizacao_interativa():
    """
    Permite remover um repositório da lista
    de repositórios autorizados.
    """

    repositorios = carregar_autorizados()

    if not repositorios:
        print(
            "\nNenhum repositório autorizado."
        )
        return

    print("\nRepositórios autorizados:\n")

    for indice, repositorio in enumerate(
        repositorios,
        start=1,
    ):
        print(
            f"{indice}. {repositorio}"
        )

    escolha = input(
        "\nSelecione o repositório "
        "para revogar a autorização: "
    ).strip()

    if not escolha.isdigit():
        print("\nSeleção inválida.")
        return

    indice = int(escolha)

    if not 1 <= indice <= len(repositorios):
        print("\nRepositório inválido.")
        return

    repositorio = repositorios[
        indice - 1
    ]

    aprovado = solicitar_aprovacao(
        "Revogar autorização do repositório",
        [
            f"Repositório: {repositorio}",
            (
                "O agente deixará de executar "
                "alterações nesse repositório."
            ),
            (
                "Nenhum arquivo ou repositório "
                "será excluído."
            ),
        ],
    )

    if not aprovado:
        print(
            "\nRevogação cancelada."
        )
        return

    revogar_repositorio(
        repositorio
    )

    print(
        f"\nAutorização de "
        f"'{repositorio}' revogada."
    )