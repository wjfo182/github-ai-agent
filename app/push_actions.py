from app.approvals import solicitar_aprovacao

from app.git_manager import (
    clonar_repositorio,
    obter_branch_atual,
    repositorio_esta_limpo,
    atualizar_todas_referencias,
    branch_remota_existe,
    obter_sincronizacao,
    obter_commits_para_push,
    obter_historico_recente,
    executar_push,
    publicar_nova_branch,
)

from app.repository_selector import selecionar_repositorio


def publicar_branch_atual():
    """
    Publica a branch atual de um repositório
    autorizado.

    Não utiliza force push.
    """

    nome_completo = selecionar_repositorio()

    repo = clonar_repositorio(
        nome_completo
    )

    branch = obter_branch_atual(
        repo
    )

    if not branch:
        print(
            "\nO repositório está em detached HEAD."
        )
        print(
            "O push foi bloqueado."
        )
        return

    print(
        f"\nRepositório: {nome_completo}"
    )

    print(
        f"Branch atual: {branch}"
    )

    # Não publicar com arquivos locais pendentes.
    if not repositorio_esta_limpo(repo):
        print(
            "\nExistem alterações locais não commitadas."
        )
        print(
            "O push foi bloqueado por segurança."
        )
        return

    print(
        "\nAtualizando referências remotas..."
    )

    atualizar_todas_referencias(
        repo
    )

    existe_remotamente = branch_remota_existe(
        repo,
        branch,
    )

    # -------------------------------------------------
    # CASO 1: branch remota ainda não existe
    # -------------------------------------------------

    if not existe_remotamente:
        print(
            f"\nA branch '{branch}' ainda não "
            "existe no GitHub."
        )

        historico = obter_historico_recente(
            repo,
            limite=10,
        )

        print("\nCommits recentes da branch:")

        print(
            historico
            or "Nenhum commit encontrado."
        )

        aprovado = solicitar_aprovacao(
            "Publicar nova branch no GitHub",
            [
                f"Repositório: {nome_completo}",
                f"Criar a branch remota '{branch}'.",
                (
                    "Configurar origin como upstream "
                    "da branch local."
                ),
                "Nenhuma outra branch será alterada.",
                "Nenhum force push será utilizado.",
            ],
        )

        if not aprovado:
            print(
                "\nPublicação cancelada."
            )
            return

        resultado = publicar_nova_branch(
            repo,
            branch,
        )

        print("\n" + "=" * 60)
        print("NOVA BRANCH PUBLICADA")
        print("=" * 60)

        if resultado:
            print(resultado)

        print(
            f"\nA branch '{branch}' agora existe "
            "no GitHub."
        )

        return

    # -------------------------------------------------
    # CASO 2: branch já existe no GitHub
    # -------------------------------------------------

    sincronizacao = obter_sincronizacao(
        repo,
        branch,
    )

    print("\nEstado de sincronização:")

    print(
        f"  Commits à frente: "
        f"{sincronizacao['frente']}"
    )

    print(
        f"  Commits atrás: "
        f"{sincronizacao['atras']}"
    )

    # Se o GitHub recebeu commits que não temos
    # localmente, não tentamos publicar.
    if sincronizacao["atras"] > 0:
        print(
            "\n[!] A branch remota possui commits "
            "que não existem localmente."
        )

        print(
            "O push foi bloqueado para evitar "
            "sobrescrever ou causar conflitos."
        )

        return

    if sincronizacao["frente"] == 0:
        print(
            "\nA branch local já está sincronizada "
            "com o GitHub."
        )

        print(
            "Nenhum push é necessário."
        )

        return

    commits = obter_commits_para_push(
        repo,
        branch,
    )

    print("\n" + "=" * 60)
    print("COMMITS QUE SERÃO PUBLICADOS")
    print("=" * 60)

    print(
        commits
        or "Nenhum commit identificado."
    )

    aprovado = solicitar_aprovacao(
        "Publicar commits no GitHub",
        [
            f"Repositório: {nome_completo}",
            f"Branch: {branch}",
            (
                f"Publicar {sincronizacao['frente']} "
                "commit(s)."
            ),
            "Esta ação modificará o GitHub remoto.",
            "Nenhum force push será utilizado.",
            "Nenhuma outra branch será alterada.",
        ],
    )

    if not aprovado:
        print(
            "\nPublicação cancelada."
        )
        return

    resultado = executar_push(
        repo,
        branch,
    )

    print("\n" + "=" * 60)
    print("PUSH CONCLUÍDO")
    print("=" * 60)

    if resultado:
        print(resultado)

    # Confirmação pós-push
    atualizar_todas_referencias(
        repo
    )

    sincronizacao_final = obter_sincronizacao(
        repo,
        branch,
    )

    print("\nEstado após publicação:")

    print(
        f"  À frente: "
        f"{sincronizacao_final['frente']}"
    )

    print(
        f"  Atrás: "
        f"{sincronizacao_final['atras']}"
    )

    if (
        sincronizacao_final["frente"] == 0
        and sincronizacao_final["atras"] == 0
    ):
        print(
            "\nBranch local e GitHub estão "
            "sincronizados."
        )


def main():
    try:
        publicar_branch_atual()

    except (RuntimeError, ValueError) as erro:
        print(
            f"\nNão foi possível realizar "
            f"a publicação: {erro}"
        )


if __name__ == "__main__":
    main()