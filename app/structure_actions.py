from pathlib import Path

from app.approvals import (
    solicitar_aprovacao,
)

from app.git_manager import (
    clonar_repositorio,
    repositorio_esta_limpo,
    atualizar_todas_referencias,
    selecionar_branch,
    atualizar_branch_local_ff,
    mover_arquivo_local_sem_stage,
    obter_revisao_local,
)

from app.security import (
    validar_organizacao_estrutura,
)


def executar_organizar_estrutura(
    nome_completo,
    analise,
    proposta,
):
    """
    Organiza somente movimentos Java previamente
    permitidos pela política de segurança.

    Não modifica código-fonte.
    Não altera packages.
    Não realiza commit.
    Não realiza push.
    """

    if proposta.tipo != "organizar_estrutura":
        raise RuntimeError(
            "Executor recebeu ação incompatível."
        )

    movimentos = validar_organizacao_estrutura(
        analise
    )

    branch = analise[
        "branch_analise"
    ]

    print("\n" + "=" * 60)
    print("PLANO DE ORGANIZAÇÃO")
    print("=" * 60)

    print(
        f"\nRepositório: {nome_completo}"
    )

    print(
        f"Branch: {branch}"
    )

    print("\nMovimentos propostos:")

    for movimento in movimentos:
        print(
            f"\n  {movimento['origem']}"
        )

        print("       ↓")

        print(
            f"  {movimento['destino']}"
        )

    print(
        "\nNenhum conteúdo Java será alterado."
    )

    print(
        "Nenhum package será criado ou modificado."
    )

    aprovado = solicitar_aprovacao(
        "Organizar estrutura Java",
        [
            f"Repositório: {nome_completo}",
            f"Branch: {branch}",
            (
                f"Arquivos a mover: "
                f"{len(movimentos)}"
            ),
            "Utilizar git mv.",
            "Não alterar conteúdo dos arquivos.",
            "Não realizar commit.",
            "Não realizar push.",
        ],
    )

    if not aprovado:
        print(
            "\nOrganização cancelada."
        )
        return

    repo = clonar_repositorio(
        nome_completo
    )

    if not repositorio_esta_limpo(
        repo
    ):
        raise RuntimeError(
            "Existem alterações locais. "
            "Organização bloqueada."
        )

    atualizar_todas_referencias(
        repo
    )

    selecionar_branch(
        repo,
        branch,
    )

    atualizar_branch_local_ff(
        repo,
        branch,
    )

    raiz = Path(repo).resolve()

    # -----------------------------------------
    # Pré-validação de TODO o plano
    # antes do primeiro movimento
    # -----------------------------------------

    for movimento in movimentos:

        origem = (
            raiz
            / movimento["origem"]
        ).resolve()

        destino = (
            raiz
            / movimento["destino"]
        ).resolve()

        try:
            origem.relative_to(raiz)
            destino.relative_to(raiz)

        except ValueError as erro:
            raise RuntimeError(
                "Plano contém caminho inválido."
            ) from erro

        if not origem.is_file():
            raise RuntimeError(
                "Arquivo de origem não existe: "
                f"{movimento['origem']}"
            )

        if destino.exists():
            raise RuntimeError(
                "Arquivo de destino já existe: "
                f"{movimento['destino']}"
            )

    # -----------------------------------------
    # Executar movimentos
    # -----------------------------------------

    for movimento in movimentos:

        mover_arquivo_local_sem_stage(
            repo,
            movimento["origem"],
            movimento["destino"],
        )

    print("\n" + "=" * 60)
    print("ESTRUTURA ORGANIZADA LOCALMENTE")
    print("=" * 60)

    print(
        obter_revisao_local(
            repo
        )
    )

    print(
        "\nNenhum commit foi realizado."
    )

    print(
        "Nenhum push foi realizado."
    )