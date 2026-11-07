from app.approvals import solicitar_aprovacao

from app.github_client import obter_repositorio

from app.git_manager import (
    clonar_repositorio,
    selecionar_branch,
    repositorio_esta_limpo,
    escrever_arquivo_local,
    obter_revisao_local,
)

from app.readme_generator import gerar_readme_basico

from app.repository import analisar_portfolio_repositorio

from app.repository_selector import selecionar_repositorio


def criar_readme_local():
    """
    Cria um README.md somente na cópia local
    de um repositório autorizado.
    """

    # 1. Usuário escolhe um repositório autorizado
    nome_completo = selecionar_repositorio()

    print(
        f"\nAnalisando {nome_completo}..."
    )

    # 2. Descobrir estrutura e branch apropriada
    analise = analisar_portfolio_repositorio(
        nome_completo
    )

    branch = analise["branch_analise"]

    dados_branch = analise[
        "analise_branches"
    ]["branches"][branch]

    # 3. Evitar sobrescrever README existente
    if dados_branch["possui_readme"]:
        print(
            f"\nA branch '{branch}' já possui README.md."
        )

        print(
            "Nenhuma alteração foi realizada."
        )

        return

    # 4. Buscar informações do repositório
    dados_repo = obter_repositorio(
        nome_completo
    )

    descricao = dados_repo.get(
        "description"
    )

    linguagens = dados_branch.get(
        "linguagens",
        [],
    )

    nome_projeto = nome_completo.split("/")[-1]

    # 5. Preparar cópia local
    repo = clonar_repositorio(
        nome_completo
    )

    if not repositorio_esta_limpo(repo):
        print(
            "\nExistem alterações locais não commitadas."
        )

        print(
            "A operação foi bloqueada por segurança."
        )

        return

    selecionar_branch(
        repo,
        branch,
    )

    # 6. Gerar conteúdo
    conteudo = gerar_readme_basico(
        nome_projeto,
        descricao,
        linguagens,
    )

    print("\n" + "=" * 60)
    print("PRÉVIA DO README")
    print("=" * 60)

    print(conteudo)

    # 7. Aprovação explícita
    aprovado = solicitar_aprovacao(
        "Criar README.md local",
        [
            f"Repositório: {nome_completo}",
            f"Branch: {branch}",
            "Criar um novo README.md.",
            "Alteração somente na cópia local.",
            "Não realizar commit.",
            "Não realizar push.",
        ],
    )

    if not aprovado:
        print("\nOperação cancelada.")
        return

    # 8. Escrever arquivo
    caminho = escrever_arquivo_local(
        repo,
        "README.md",
        conteudo,
    )

    print("\nREADME criado localmente.")
    print(f"Arquivo: {caminho}")

    # 9. Mostrar revisão
    revisao = obter_revisao_local(
        repo
    )

    print("\n" + "=" * 60)
    print("REVISÃO LOCAL")
    print("=" * 60)

    for arquivo in revisao["arquivos_novos"]:
        print(
            f"\n--- {arquivo['caminho']} ---"
        )

        print(
            arquivo["conteudo"]
        )

    print("\nNenhum commit foi realizado.")
    print("Nenhum push foi realizado.")


def main():
    criar_readme_local()


if __name__ == "__main__":
    main()