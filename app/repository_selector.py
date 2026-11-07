from app.github_client import listar_repositorios

from app.permissions import (
    autorizar_repositorio,
    repositorio_autorizado,
)


def selecionar_repositorio():
    """
    Lista os repositórios acessíveis e permite
    selecionar um deles.
    """

    repositorios = listar_repositorios()

    if not repositorios:
        raise RuntimeError(
            "Nenhum repositório encontrado."
        )

    print("\nRepositórios disponíveis:\n")

    for indice, repo in enumerate(
        repositorios,
        start=1,
    ):
        autorizado = repositorio_autorizado(
            repo["nameWithOwner"]
        )

        status = (
            "AUTORIZADO"
            if autorizado
            else "NÃO AUTORIZADO"
        )

        print(
            f"{indice}. "
            f"{repo['nameWithOwner']} "
            f"[{status}]"
        )

    escolha = input(
        "\nSelecione o repositório: "
    ).strip()

    if not escolha.isdigit():
        raise ValueError(
            "Informe um número válido."
        )

    indice = int(escolha)

    if not 1 <= indice <= len(repositorios):
        raise ValueError(
            "Repositório inválido."
        )

    nome_completo = repositorios[
        indice - 1
    ]["nameWithOwner"]

    if not repositorio_autorizado(
        nome_completo
    ):
        print(
            f"\n'{nome_completo}' ainda não está "
            "autorizado para alterações."
        )

        resposta = input(
            "Autorizar este repositório? [s/n]: "
        ).strip().lower()

        if resposta not in {
            "s",
            "sim",
        }:
            raise RuntimeError(
                "Repositório não autorizado."
            )

        autorizar_repositorio(
            nome_completo
        )

        print(
            "\nRepositório autorizado."
        )

    return nome_completo
