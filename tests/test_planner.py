
from app.planner import gerar_plano_portfolio


def criar_analise_exemplo():
    """
    Simula um repositório Java.

    Não consulta GitHub nem Ollama.
    """

    return {
        "dados_repositorio": {
            "isPrivate": False,
            "repositoryTopics": ["java"],
        },
        "java_backend": {
            "java": True,
            "estrutura_java_padrao": True,
        },
        "stack_java": {
            "build_tool": "Maven",
        },
        "elegibilidade_testes": {
            "elegivel": True,
            "possui_testes": True,
        },
        "branch_analise": "main",
        "analise_branches": {
            "branches": {
                "main": {
                    "possui_readme": True,
                }
            }
        },
    }


def tipos_do_plano(analise):
    plano = gerar_plano_portfolio(analise)
    return [etapa["tipo"] for etapa in plano]


def test_projeto_completo_nao_precisa_de_acoes():
    analise = criar_analise_exemplo()

    assert gerar_plano_portfolio(analise) == []


def test_projeto_sem_maven_recebe_acao_correta():
    analise = criar_analise_exemplo()
    analise["stack_java"]["build_tool"] = None

    tipos = tipos_do_plano(analise)

    assert "configurar_build" in tipos
    assert "adicionar_testes" not in tipos


def test_projeto_sem_estrutura_java():
    analise = criar_analise_exemplo()
    analise["java_backend"]["estrutura_java_padrao"] = False

    tipos = tipos_do_plano(analise)

    assert "organizar_estrutura" in tipos


def test_projeto_sem_testes():
    analise = criar_analise_exemplo()
    analise["elegibilidade_testes"]["possui_testes"] = False

    tipos = tipos_do_plano(analise)

    assert "adicionar_testes" in tipos


def test_projeto_sem_readme():
    analise = criar_analise_exemplo()

    analise["analise_branches"]["branches"]["main"][
        "possui_readme"
    ] = False

    tipos = tipos_do_plano(analise)

    assert "criar_readme" in tipos


def test_repositorio_privado():
    analise = criar_analise_exemplo()
    analise["dados_repositorio"]["isPrivate"] = True

    tipos = tipos_do_plano(analise)

    assert "revisar_visibilidade" in tipos


def test_repositorio_sem_topics():
    analise = criar_analise_exemplo()
    analise["dados_repositorio"]["repositoryTopics"] = []

    tipos = tipos_do_plano(analise)

    assert "adicionar_topics" in tipos
