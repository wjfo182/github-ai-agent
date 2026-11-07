import difflib
from pathlib import Path

from app.approvals import (
    solicitar_aprovacao,
)

from app.build_generator import (
    gerar_pom_maven,
)

from app.git_manager import (
    clonar_repositorio,
    repositorio_esta_limpo,
    atualizar_todas_referencias,
    selecionar_branch,
    atualizar_branch_local_ff,
    escrever_arquivo_local,
    obter_revisao_local,
)

from app.security import (
    validar_configuracao_build,
)


def gerar_diff_pom(
    conteudo,
):
    """
    Gera um diff para um pom.xml novo.
    """

    linhas = conteudo.splitlines(
        keepends=True
    )

    return "".join(
        difflib.unified_diff(
            [],
            linhas,
            fromfile="/dev/null",
            tofile="b/pom.xml",
        )
    )


def escolher_java_release():
    """
    Solicita uma versão Java explicitamente.

    O agente não adivinha qual JDK o usuário deseja.
    """

    opcoes = {
    "1": "8",
    "2": "11",
    "3": "17",
    "4": "21",
    "5": "25",
    "6": "26",
}
    
    print("\nVersão Java para o Maven:\n")
    print("1. Java 8")
    print("2. Java 11")
    print("3. Java 17")
    print("4. Java 21")
    print("5. Java 25")
    print("6. Java 26")

    
    escolha = input(
        "\nEscolha uma opção: "
    ).strip()

    java_release = opcoes.get(
        escolha
    )

    if java_release is None:
        raise RuntimeError(
            "Versão Java inválida."
        )

    return java_release


def executar_configurar_build(
    nome_completo,
    analise,
    proposta,
):
    """
    Configura Maven de forma determinística.

    Não move arquivos.
    Não realiza commit.
    Não realiza push.
    """

    if proposta.tipo != "configurar_build":
        raise RuntimeError(
            "Executor recebeu ação incompatível."
        )

    validar_configuracao_build(
        analise
    )

    branch = analise[
        "branch_analise"
    ]

    java_release = escolher_java_release()

    pom = gerar_pom_maven(
        nome_completo,
        java_release,
    )

    diff = gerar_diff_pom(
        pom
    )

    print("\n" + "=" * 60)
    print("CONFIGURAÇÃO MAVEN PROPOSTA")
    print("=" * 60)

    print(
        f"\nRepositório: {nome_completo}"
    )

    print(
        f"Branch: {branch}"
    )

    print(
        f"Java: {java_release}"
    )

    print(
        "\nO agente criará somente:"
    )

    print(
        "  pom.xml"
    )

    if not analise[
        "java_backend"
    ].get("estrutura_java_padrao"):

        print(
            "\n[!] Atenção: o projeto ainda não usa "
            "src/main/java."
        )

        print(
            "O pom.xml será criado, mas a organização "
            "dos arquivos será tratada em outra ação."
        )

    print("\n" + "=" * 60)
    print("DIFF PROPOSTO")
    print("=" * 60)

    print(diff)

    aprovado = solicitar_aprovacao(
        "Criar configuração Maven",
        [
            f"Repositório: {nome_completo}",
            f"Branch: {branch}",
            "Arquivo novo: pom.xml",
            f"Java release: {java_release}",
            "Adicionar JUnit para testes.",
            "Não mover código.",
            "Não realizar commit.",
            "Não realizar push.",
        ],
    )

    if not aprovado:
        print(
            "\nConfiguração cancelada."
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
            "Configuração bloqueada."
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

    caminho_pom = (
        Path(repo) / "pom.xml"
    ).resolve()

    raiz = Path(repo).resolve()

    try:
        caminho_pom.relative_to(
            raiz
        )

    except ValueError as erro:
        raise RuntimeError(
            "Caminho do pom.xml inválido."
        ) from erro

    if caminho_pom.exists():
        raise RuntimeError(
            "pom.xml já existe. "
            "Nenhum arquivo será sobrescrito."
        )

    escrever_arquivo_local(
        repo,
        "pom.xml",
        pom,
        sobrescrever=False,
    )

    print("\n" + "=" * 60)
    print("MAVEN CONFIGURADO LOCALMENTE")
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