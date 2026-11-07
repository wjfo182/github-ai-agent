from app.git_manager import (
    clonar_repositorio,
    atualizar_todas_referencias,
    obter_merge_base,
    obter_commits_exclusivos,
)


def diagnosticar_branches():
    nome_completo = "wjfo182/Estudos-Java"

    repo = clonar_repositorio(
        nome_completo
    )

    atualizar_todas_referencias(
        repo
    )

    branch_main = "origin/main"
    branch_master = "origin/master"

    merge_base = obter_merge_base(
        repo,
        branch_main,
        branch_master,
    )

    commits = obter_commits_exclusivos(
        repo,
        branch_main,
        branch_master,
    )

    print("\n" + "=" * 60)
    print("DIAGNÓSTICO DE BRANCHES")
    print("=" * 60)

    print(f"\nBranch A: {branch_main}")
    print(f"Branch B: {branch_master}")

    if merge_base:
        print(
            "\nAs branches possuem "
            "um ancestral comum."
        )

        print(
            f"Merge base: {merge_base}"
        )
    else:
        print(
            "\n[!] As branches não possuem "
            "um ancestral comum detectado."
        )

        print(
            "Isso pode indicar históricos "
            "criados separadamente."
        )

    print(
        f"\nCommits exclusivos de "
        f"{branch_main}:"
    )

    print(
        commits[branch_main]
        or "Nenhum"
    )

    print(
        f"\nCommits exclusivos de "
        f"{branch_master}:"
    )

    print(
        commits[branch_master]
        or "Nenhum"
    )

    print(
        "\nNenhuma branch foi alterada."
    )


def main():
    diagnosticar_branches()


if __name__ == "__main__":
    main()
