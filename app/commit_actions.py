from app.approvals import solicitar_aprovacao

from app.git_manager import (
    clonar_repositorio,
    obter_branch_atual,
    listar_arquivos_stage,
    listar_arquivos_para_commit,
    adicionar_caminho_stage,
    remover_caminho_stage,
    obter_diff_stage,
    criar_commit_local,
    obter_status_git,
)

from app.repository_selector import selecionar_repositorio

from app.git_manager import obter_head_commit

from app.permissions import exigir_repositorio_autorizado

def escolher_arquivos(arquivos):
    """
    Permite escolher quais alterações serão
    incluídas no commit.
    """

    print("\nAlterações locais encontradas:\n")

    for indice, arquivo in enumerate(
        arquivos,
        start=1,
    ):
        print(f"{indice}. {arquivo}")

    print(
        "\nDigite os números separados por vírgula."
    )

    print(
        "Ou digite 'todos' para selecionar tudo."
    )

    escolha = input(
        "\nArquivos para o commit: "
    ).strip().lower()

    if escolha in {
        "todos",
        "t",
    }:
        return arquivos

    partes = [
        parte.strip()
        for parte in escolha.split(",")
    ]

    selecionados = []

    for parte in partes:

        if not parte.isdigit():
            raise ValueError(
                f"Seleção inválida: {parte}"
            )

        indice = int(parte)

        if not 1 <= indice <= len(arquivos):
            raise ValueError(
                f"Número fora da lista: {indice}"
            )

        arquivo = arquivos[indice - 1]

        if arquivo not in selecionados:
            selecionados.append(arquivo)

    if not selecionados:
        raise ValueError(
            "Nenhum arquivo foi selecionado."
        )

    return selecionados

def criar_commit_controlado():
    """
    Cria um commit local em um repositório
    autorizado.

    Não realiza push.

    Se uma operação falhar antes da confirmação
    do commit, tenta desfazer o staging realizado
    pelo próprio agente.

    As alterações dos arquivos são preservadas.
    """

    nome_completo = selecionar_repositorio()

# Verificar autorização ANTES de qualquer
# operação sobre o repositório.
    exigir_repositorio_autorizado(
        nome_completo
)

    repo = clonar_repositorio(
        nome_completo
)

    branch = obter_branch_atual(repo)

    if not branch:
        print(
            "\nO repositório está em detached HEAD."
        )
        print(
            "O commit foi bloqueado."
        )
        return

    print(
        f"\nRepositório: {nome_completo}"
    )

    print(
        f"Branch atual: {branch}"
    )

    # -------------------------------------------------
    # 1. Verificar staging existente
    # -------------------------------------------------

    arquivos_stage = listar_arquivos_stage(
        repo
    )

    if arquivos_stage:
        print(
            "\nJá existem arquivos no staging:"
        )

        for arquivo in arquivos_stage:
            print(f"  - {arquivo}")

        print(
            "\nO commit foi bloqueado para evitar "
            "misturar alterações."
        )
        return

    # -------------------------------------------------
    # 2. Selecionar arquivos
    # -------------------------------------------------

    arquivos = listar_arquivos_para_commit(
        repo
    )

    if not arquivos:
        print(
            "\nNenhuma alteração local encontrada."
        )
        return

    selecionados = escolher_arquivos(
        arquivos
    )

    if not selecionados:
        print(
            "\nNenhum arquivo selecionado. "
            "Operação cancelada."
        )
        return

    print("\nArquivos selecionados:")

    for arquivo in selecionados:
        print(f"  - {arquivo}")

    # -------------------------------------------------
    # 3. Aprovar staging
    # -------------------------------------------------

    aprovado_stage = solicitar_aprovacao(
        "Preparar arquivos para commit",
        [
            f"Repositório: {nome_completo}",
            f"Branch: {branch}",
            (
                f"Adicionar {len(selecionados)} "
                "arquivo(s) ao staging."
            ),
            "Não realizar commit ainda.",
            "Não realizar push.",
        ],
    )

    if not aprovado_stage:
        print("\nOperação cancelada.")
        return

    # -------------------------------------------------
    # 4. Inicializar controle de recuperação
    # -------------------------------------------------

    caminhos_tentados = []
    commit_realizado = False
    diff_revisado = None
    head_antes_commit = None
    tentativa_commit = False
    staging_alterado = False

    try:

        # ---------------------------------------------
        # 5. Preparar staging
        # ---------------------------------------------

        for arquivo in selecionados:

            # Registramos antes de executar o git add:
            # se ele falhar após modificar o índice,
            # ainda tentaremos desfazer a operação.

            caminhos_tentados.append(arquivo)

            adicionar_caminho_stage(
                repo,
                arquivo,
            )

        # ---------------------------------------------
        # 6. Revisar diff
        # ---------------------------------------------

        diff = obter_diff_stage(repo)
        diff_revisado = diff
        

        print("\n" + "=" * 60)
        print("CONTEÚDO EXATO DO COMMIT")
        print("=" * 60)

        print(
            diff
            or "Nenhuma diferença encontrada."
        )

        # ---------------------------------------------
        # 7. Informar mensagem
        # ---------------------------------------------

        mensagem = input(
            "\nMensagem do commit: "
        ).strip()

        if not mensagem:

            print(
                "\nMensagem vazia. "
                "Commit cancelado."
            )

            return

        # ---------------------------------------------
        # 8. Aprovação final
        # ---------------------------------------------

        aprovado_commit = solicitar_aprovacao(
            "Criar commit local",
            [
                f"Repositório: {nome_completo}",
                f"Branch: {branch}",
                f"Mensagem: {mensagem}",
                (
                    f"Incluir {len(selecionados)} "
                    "arquivo(s)."
                ),
                "Não realizar push.",
            ],
        )

        if not aprovado_commit:

            print(
                "\nCommit cancelado."
            )

            return

        # ---------------------------------------------
        # 9. Criar commit
        # ---------------------------------------------
        # Conferir se o staging ainda corresponde
# exatamente ao diff apresentado ao usuário.

        diff_antes_commit = obter_diff_stage(repo)

        if diff_antes_commit != diff_revisado:

            staging_alterado = True

            raise RuntimeError(
                "O staging mudou após a revisão. "
                "Commit bloqueado. "
                "Verifique git status antes de prosseguir."
    )

# Registrar o HEAD imediatamente antes
# da tentativa de commit.

        head_antes_commit = obter_head_commit(repo)

        tentativa_commit = True

        resultado = criar_commit_local(
            repo,
            mensagem,
        )

        # Marcar sucesso imediatamente após
        # a função de commit retornar.
        commit_realizado = True

        print("\n" + "=" * 60)
        print("COMMIT LOCAL CRIADO")
        print("=" * 60)

        print(resultado)

        print("\nStatus atual:")
        print(obter_status_git(repo))

        print(
            "\nNenhum push foi realizado."
        )

    
    finally:

        if (
            not commit_realizado
            and caminhos_tentados
        ):

            pode_limpar = not staging_alterado

            # -------------------------------------
            # 1. Verificar resultado do commit
            # -------------------------------------

            if tentativa_commit:

                try:
                    head_depois = obter_head_commit(
                        repo
                    )

                except Exception as erro:

                    pode_limpar = False

                    print(
                        "\nNão foi possível verificar "
                        f"o HEAD: {erro}"
                    )

                else:

                    if (
                        head_depois
                        != head_antes_commit
                    ):

                        pode_limpar = False

                        print(
                            "\nATENÇÃO: o HEAD mudou "
                            "durante a operação."
                        )

                        print(
                            "O commit pode ter sido criado."
                        )

            # -------------------------------------
            # 2. Verificar integridade do staging
            # -------------------------------------

            if (
                pode_limpar
                and diff_revisado is not None
            ):

                try:
                    diff_atual = obter_diff_stage(
                        repo
                    )

                except Exception as erro:

                    pode_limpar = False

                    print(
                        "\nNão foi possível verificar "
                        f"o staging: {erro}"
                    )

                else:

                    if diff_atual != diff_revisado:

                        pode_limpar = False

                        print(
                            "\nO staging mudou durante "
                            "a operação."
                        )

            # -------------------------------------
            # 3. Recuperação ou inspeção manual
            # -------------------------------------

            if not pode_limpar:

                print(
                    "\nRecuperação automática "
                    "interrompida por segurança."
                )

                print(
                    "Consulte git status e git log "
                    "antes de repetir a operação."
                )

            else:

                print(
                    "\nRecuperando staging "
                    "da operação..."
                )

                falhas_limpeza = []

                for arquivo in reversed(
                    caminhos_tentados
                ):

                    try:
                        remover_caminho_stage(
                            repo,
                            arquivo,
                        )

                    except Exception as erro:

                        falhas_limpeza.append(
                            (arquivo, erro)
                        )

                if falhas_limpeza:

                    print(
                        "\nATENÇÃO: a recuperação "
                        "foi incompleta."
                    )

                    for arquivo, erro in falhas_limpeza:
                        print(
                            f"  - {arquivo}: {erro}"
                        )

                    print(
                        "Inspecione o staging "
                        "manualmente."
                    )

                else:

                    print(
                        "Staging da operação removido."
                    )

                    print(
                        "Alterações locais preservadas."
                    )

def main():
    try:
        criar_commit_controlado()

    except (RuntimeError, ValueError) as erro:
        print(
            f"\nNão foi possível criar o commit: "
            f"{erro}"
        )


if __name__ == "__main__":
    main()