from app.approvals import solicitar_aprovacao

from app.git_manager import (
    clonar_repositorio,
    repositorio_esta_limpo,
    atualizar_todas_referencias,
    obter_hash_ref,
    obter_merge_base,
    obter_commits_para_push,
    obter_arquivos_diferentes,
    atualizar_branch_remota,
)


def atualizar_main():
    nome_completo = "wjfo182/Estudos-Java"

    branch_integracao = "integracao-main-master"
    branch_destino = "main"

    repo = clonar_repositorio(
        nome_completo
    )

    if not repositorio_esta_limpo(repo):
        print(
            "\nExistem alterações locais "
            "não commitadas."
        )
        print(
            "A atualização da main foi bloqueada."
        )
        return

    print(
        "\nAtualizando referências do GitHub..."
    )

    atualizar_todas_referencias(repo)

    hash_main = obter_hash_ref(
        repo,
        "origin/main",
    )

    hash_integracao_local = obter_hash_ref(
        repo,
        branch_integracao,
    )

    hash_integracao_remota = obter_hash_ref(
        repo,
        "origin/integracao-main-master",
    )

    # Proteção:
    # a branch local deve ser exatamente a mesma
    # que já foi publicada e revisada no GitHub.
    if hash_integracao_local != hash_integracao_remota:
        print(
            "\nA branch de integração local é "
            "diferente da versão remota."
        )
        print(
            "A atualização foi bloqueada."
        )
        return

    merge_base = obter_merge_base(
        repo,
        "origin/main",
        branch_integracao,
    )

    # Para fast-forward seguro, o ancestral comum
    # precisa ser exatamente o HEAD atual da main.
    if merge_base != hash_main:
        print(
            "\nA main não pode mais ser atualizada "
            "por fast-forward."
        )
        print(
            "O GitHub pode ter recebido novas "
            "alterações desde a última análise."
        )
        print(
            "A operação foi bloqueada."
        )
        return

    commits = obter_commits_para_push(
        repo,
        branch_integracao,
    )

    arquivos = obter_arquivos_diferentes(
        repo,
        "origin/main",
        branch_integracao,
    )

    print("\n" + "=" * 60)
    print("ATUALIZAÇÃO PROPOSTA PARA MAIN")
    print("=" * 60)

    print(
        f"\nRepositório: {nome_completo}"
    )

    print(
        f"Main atual: "
        f"{hash_main[:8]}"
    )

    print(
        f"Nova versão: "
        f"{hash_integracao_local[:8]}"
    )

    print("\nCommits que serão incorporados:")

    print(
        commits
        or "Nenhum commit identificado."
    )

    print("\nArquivos afetados:")

    print(
        arquivos
        or "Nenhuma diferença encontrada."
    )

    aprovado = solicitar_aprovacao(
        "Atualizar a branch main",
        [
            (
                "Atualizar origin/main para o "
                "conteúdo validado da branch "
                "integracao-main-master."
            ),
            "A atualização será fast-forward.",
            "Nenhum force push será utilizado.",
            "A branch master não será excluída.",
            (
                "A branch integracao-main-master "
                "não será excluída."
            ),
            (
                "Esta ação modificará a branch "
                "main no GitHub."
            ),
        ],
    )

    if not aprovado:
        print("\nAtualização cancelada.")
        return

    resultado = atualizar_branch_remota(
        repo,
        branch_integracao,
        branch_destino,
    )

    print("\n" + "=" * 60)
    print("MAIN ATUALIZADA")
    print("=" * 60)

    if resultado:
        print(resultado)

    # Atualiza novamente nossas referências locais
    # para conferir o resultado remoto.
    atualizar_todas_referencias(repo)

    novo_hash_main = obter_hash_ref(
        repo,
        "origin/main",
    )

    if novo_hash_main == hash_integracao_local:
        print(
            "\nVerificação concluída: "
            "origin/main aponta para a "
            "integração validada."
        )
    else:
        print(
            "\n[!] O hash remoto não corresponde "
            "ao esperado."
        )

    print(
        "\nmaster permanece intacta."
    )

    print(
        "integracao-main-master permanece intacta."
    )


def main():
    atualizar_main()


if __name__ == "__main__":
    main()