from app.approvals import solicitar_aprovacao

from app.github_client import obter_repositorio

from app.git_manager import (
    clonar_repositorio,
    repositorio_esta_limpo,
    atualizar_todas_referencias,
    branch_e_ancestral,
    excluir_branch_remota,
    atualizar_main_local,
    excluir_branch_local,
)


def limpar_branches_auxiliares():
    nome_completo = "wjfo182/Estudos-Java"

    branches_remover = [
        "master",
        "integracao-main-master",
    ]

    repo = clonar_repositorio(
        nome_completo
    )

    if not repositorio_esta_limpo(repo):
        print(
            "\nExistem alterações locais não commitadas."
        )
        print(
            "A limpeza foi bloqueada por segurança."
        )
        return

    dados_repo = obter_repositorio(
        nome_completo
    )

    branch_info = dados_repo.get(
        "defaultBranchRef"
    )

    branch_padrao = (
        branch_info.get("name")
        if branch_info
        else None
    )

    if branch_padrao != "main":
        print(
            "\nA branch padrão do GitHub não é main."
        )
        print(
            "A exclusão foi bloqueada."
        )
        return

    print(
        "\nAtualizando referências remotas..."
    )

    atualizar_todas_referencias(
        repo
    )

    print("\nVerificando históricos...")

    for branch in branches_remover:
        origem = f"origin/{branch}"

        integrada = branch_e_ancestral(
            repo,
            origem,
            "origin/main",
        )

        if not integrada:
            print(
                f"\n[!] A branch '{branch}' possui "
                "histórico que não está contido na main."
            )

            print(
                "Nenhuma branch será excluída."
            )
            return

        print(
            f"[+] {branch}: histórico preservado na main."
        )

    print("\n" + "=" * 60)
    print("LIMPEZA PROPOSTA")
    print("=" * 60)

    print(
        "\nBranch definitiva: main"
    )

    print("\nBranches candidatas à exclusão:")
    print("  - master")
    print("  - integracao-main-master")

    print(
        "\nTodos os commits dessas branches "
        "já estão contidos em origin/main."
    )

    aprovado = solicitar_aprovacao(
        "Excluir branches auxiliares do GitHub",
        [
            "Manter a branch main.",
            "Excluir a branch remota master.",
            (
                "Excluir a branch remota "
                "integracao-main-master."
            ),
            (
                "Os históricos já foram verificados "
                "como presentes na main."
            ),
            "Nenhum force push será utilizado.",
        ],
    )

    if not aprovado:
        print("\nLimpeza cancelada.")
        return

    for branch in branches_remover:
        print(
            f"\nExcluindo origin/{branch}..."
        )

        resultado = excluir_branch_remota(
            repo,
            branch,
        )

        if resultado:
            print(resultado)

    atualizar_todas_referencias(
        repo
    )

    atualizar_main_local(
        repo
    )

    for branch in branches_remover:
        try:
            excluir_branch_local(
                repo,
                branch,
            )

            print(
                f"[+] Branch local '{branch}' removida."
            )

        except RuntimeError as erro:
            print(
                f"[!] Não foi possível remover "
                f"a branch local '{branch}': {erro}"
            )

    print("\n" + "=" * 60)
    print("LIMPEZA CONCLUÍDA")
    print("=" * 60)

    print(
        "\nA branch main foi preservada."
    )

    print(
        "As branches auxiliares foram removidas "
        "quando seguro."
    )


def main():
    limpar_branches_auxiliares()


if __name__ == "__main__":
    main()