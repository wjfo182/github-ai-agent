from app.approvals import solicitar_aprovacao

from app.git_manager import (
    clonar_repositorio,
    obter_branch_atual,
    repositorio_esta_limpo,
    branch_remota_existe,
    publicar_nova_branch,
)


def publicar_branch_integracao():
    nome_completo = "wjfo182/Estudos-Java"
    branch = "integracao-main-master"

    repo = clonar_repositorio(nome_completo)

    branch_atual = obter_branch_atual(repo)

    if branch_atual != branch:
        print(
            f"\nBranch atual inesperada: {branch_atual}"
        )
        print(
            f"Esperado: {branch}"
        )
        return

    if not repositorio_esta_limpo(repo):
        print(
            "\nExistem alterações locais não commitadas."
        )
        print(
            "A publicação foi bloqueada."
        )
        return

    if branch_remota_existe(repo, branch):
        print(
            f"\nA branch remota '{branch}' já existe."
        )
        print(
            "Nenhuma publicação foi realizada."
        )
        return

    aprovado = solicitar_aprovacao(
        "Publicar branch de integração",
        [
            f"Repositório: {nome_completo}",
            f"Criar no GitHub a branch '{branch}'.",
            "A branch main não será alterada.",
            "A branch master não será alterada.",
            "Nenhuma branch será excluída.",
        ],
    )

    if not aprovado:
        print("\nPublicação cancelada.")
        return

    resultado = publicar_nova_branch(
        repo,
        branch,
    )

    print("\n" + "=" * 60)
    print("BRANCH DE INTEGRAÇÃO PUBLICADA")
    print("=" * 60)

    if resultado:
        print(resultado)

    print(
        f"\nA branch '{branch}' agora existe "
        "no GitHub."
    )

    print(
        "main e master continuam inalteradas."
    )


def main():
    publicar_branch_integracao()


if __name__ == "__main__":
    main()