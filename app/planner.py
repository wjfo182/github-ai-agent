def repositorio_tem_topics(repo):
    """
    Normaliza diferentes formatos possíveis
    retornados pelo GitHub para repositoryTopics.
    """

    topics = repo.get(
        "repositoryTopics"
    )

    if not topics:
        return False

    if isinstance(topics, list):
        return len(topics) > 0

    if isinstance(topics, dict):

        nodes = topics.get(
            "nodes"
        )

        if isinstance(nodes, list):
            return len(nodes) > 0

    return bool(topics)


def adicionar_etapa(
    plano,
    tipo,
    prioridade,
    titulo,
    motivo,
):
    """
    Adiciona uma etapa ao plano.

    O tipo da ação é definido pelo Python,
    não pela IA.
    """

    plano.append({
        "ordem": len(plano) + 1,
        "tipo": tipo,
        "prioridade": prioridade,
        "titulo": titulo,
        "motivo": motivo,
    })


def gerar_plano_portfolio(
    analise,
):
    """
    Gera deterministicamente um plano de evolução
    para o repositório.

    Não executa nenhuma ação.
    """

    plano = []

    repo = analise.get(
        "dados_repositorio",
        {},
    )

    java = analise.get(
        "java_backend",
        {},
    )

    stack = analise.get(
        "stack_java",
        {},
    )

    testes = analise.get(
        "elegibilidade_testes",
        {},
    )

    branch = analise.get(
        "branch_analise"
    )

    branches = analise.get(
        "analise_branches",
        {},
    ).get(
        "branches",
        {},
    )

    dados_branch = branches.get(
        branch,
        {},
    )

    # -------------------------------------------------
    # 1. Build
    # -------------------------------------------------

    if (
        java.get("java")
        and not stack.get("build_tool")
    ):
        adicionar_etapa(
            plano,
            tipo="configurar_build",
            prioridade="alta",
            titulo="Configurar build Java",
            motivo=(
                "Código Java foi encontrado, "
                "mas Maven ou Gradle não foi detectado."
            ),
        )

    # -------------------------------------------------
    # 2. Estrutura
    # -------------------------------------------------

    if (
        java.get("java")
        and not java.get(
            "estrutura_java_padrao"
        )
    ):
        adicionar_etapa(
            plano,
            tipo="organizar_estrutura",
            prioridade="alta",
            titulo="Organizar estrutura Java",
            motivo=(
                "O projeto ainda não utiliza "
                "src/main/java."
            ),
        )

    # -------------------------------------------------
    # 3. README
    # -------------------------------------------------

    if not dados_branch.get(
        "possui_readme",
        False,
    ):
        adicionar_etapa(
            plano,
            tipo="criar_readme",
            prioridade="alta",
            titulo="Criar documentação principal",
            motivo=(
                "README.md não foi encontrado "
                "na branch analisada."
            ),
        )

    # -------------------------------------------------
    # 4. Testes
    # -------------------------------------------------

    if (
        testes.get("elegivel")
        and not testes.get(
            "possui_testes",
            False,
        )
    ):
        adicionar_etapa(
            plano,
            tipo="adicionar_testes",
            prioridade="alta",
            titulo="Adicionar testes automatizados",
            motivo=(
                "O projeto já possui estrutura, "
                "framework e classes adequadas "
                "para testes."
            ),
        )

    # -------------------------------------------------
    # 5. Visibilidade
    # -------------------------------------------------

    if repo.get(
        "isPrivate",
        False,
    ):
        adicionar_etapa(
            plano,
            tipo="revisar_visibilidade",
            prioridade="media",
            titulo="Revisar visibilidade",
            motivo=(
                "O repositório está privado, "
                "o que pode limitar sua utilização "
                "como portfólio público."
            ),
        )

    # -------------------------------------------------
    # 6. Topics
    # -------------------------------------------------

    if not repositorio_tem_topics(
        repo
    ):
        adicionar_etapa(
            plano,
            tipo="adicionar_topics",
            prioridade="baixa",
            titulo="Adicionar topics",
            motivo=(
                "O repositório ainda não possui "
                "topics para classificação no GitHub."
            ),
        )

    return plano