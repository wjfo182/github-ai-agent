import re
from app.java_analyzer import (
    planejar_movimentos_estrutura_maven,
)

ACOES_PERMITIDAS = {
    "melhorar_readme",
    "organizar_estrutura",
    "adicionar_testes",
    "configurar_build",
    "adicionar_documentacao",
    "revisar_visibilidade",
    "adicionar_topics",
}

ACOES_BLOQUEADAS = {
    "force_push",
    "excluir_repositorio",
    "excluir_branch",
    "executar_shell",
    "executar_comando",
    "alterar_permissoes",
}

def validar_tipo_acao(tipo):
    """
    Valida se uma ação proposta pela IA
    pertence à allowlist do agente.
    """

    if tipo in ACOES_BLOQUEADAS:
        raise RuntimeError(
            f"Ação explicitamente bloqueada: {tipo}"
        )

    if tipo not in ACOES_PERMITIDAS:
        raise RuntimeError(
            f"Ação não autorizada: {tipo}"
        )

    return True

def validar_acoes(acoes):
    """
    Valida todas as ações propostas pela IA.
    """

    for acao in acoes:
        validar_tipo_acao(
            acao.tipo
        )

    return True

ACOES_EXECUTAVEIS = {
    "melhorar_readme",
    "adicionar_testes",
    "configurar_build",
    "organizar_estrutura",
}

TIPOS_TESTE_SUPORTADOS = {
    "unitario",
    "unitario_service",
}

def validar_acao_executavel(tipo):
    """
    Verifica se uma ação da IA possui
    implementação segura no agente.
    """

    validar_tipo_acao(tipo)

    if tipo not in ACOES_EXECUTAVEIS:
        raise RuntimeError(
            f"A ação '{tipo}' pode ser proposta, "
            "mas ainda não possui executor seguro."
        )

    return True

def validar_geracao_testes(analise):
    """
    Valida se o agente possui contexto suficiente
    para gerar testes automaticamente.

    Retorna somente sugestões de testes que possuem
    tipos suportados pelo agente.
    """

    elegibilidade = analise.get(
        "elegibilidade_testes",
        {},
    )

    if not elegibilidade.get("elegivel"):
        motivos = elegibilidade.get(
            "motivos_bloqueio",
            [],
        )

        detalhes = "; ".join(
            motivos
        )

        raise RuntimeError(
            "Geração de testes bloqueada. "
            f"Motivos: {detalhes}"
        )

    framework = elegibilidade.get(
        "framework_testes"
    )

    if not framework:
        raise RuntimeError(
            "Geração de testes bloqueada: "
            "framework de testes não identificado."
        )

    sugestoes = analise.get(
        "sugestoes_testes",
        [],
    )

    if not sugestoes:
        raise RuntimeError(
            "Geração de testes bloqueada: "
            "nenhuma classe apropriada foi encontrada."
        )

    sugestoes_suportadas = [
        sugestao
        for sugestao in sugestoes
        if sugestao.get("tipo_teste")
        in TIPOS_TESTE_SUPORTADOS
    ]

    if not sugestoes_suportadas:
        raise RuntimeError(
            "Foram encontradas classes candidatas, "
            "mas nenhum tipo de teste possui "
            "executor seguro implementado."
        )

    return sugestoes_suportadas

def validar_conteudo_teste_java(
    conteudo,
    classe_teste,
    package_esperado,
):
    """
    Valida estruturalmente um teste Java
    antes de permitir sua gravação.
    """

    if not conteudo:
        raise RuntimeError(
            "A IA retornou um teste vazio."
        )

    # -----------------------------------------
    # Classe esperada
    # -----------------------------------------

    padrao_classe = (
        rf"\bclass\s+"
        rf"{re.escape(classe_teste)}\b"
    )

    if not re.search(
        padrao_classe,
        conteudo,
    ):
        raise RuntimeError(
            "O teste gerado não contém "
            f"a classe esperada '{classe_teste}'."
        )

    # -----------------------------------------
    # Package
    # -----------------------------------------

    resultado_package = re.search(
        r"^\s*package\s+([\w.]+)\s*;",
        conteudo,
        re.MULTILINE,
    )

    package_encontrado = (
        resultado_package.group(1)
        if resultado_package
        else None
    )

    if package_esperado:

        if package_encontrado != package_esperado:
            raise RuntimeError(
                "Package do teste não corresponde "
                "ao package da classe original."
            )

    elif package_encontrado:
        raise RuntimeError(
            "A classe original não possui package, "
            "mas a IA criou um package no teste."
        )

    # -----------------------------------------
    # Deve ser realmente um teste
    # -----------------------------------------

    if "@Test" not in conteudo:
        raise RuntimeError(
            "Nenhum método @Test foi encontrado."
        )

    # -----------------------------------------
    # APIs proibidas nesta primeira versão
    # -----------------------------------------

    fragmentos_bloqueados = [
        "Runtime.getRuntime",
        "ProcessBuilder",
        "System.exit",
        "java.net.",
        "HttpClient",
        "Socket(",
        "Files.delete",
        ".delete()",
    ]

    for fragmento in fragmentos_bloqueados:

        if fragmento in conteudo:
            raise RuntimeError(
                "Teste bloqueado por conter "
                f"API não permitida: {fragmento}"
            )

    return True

def validar_acao_no_contexto(
    tipo,
    analise,
):
    validar_acao_executavel(
        tipo
    )

    if tipo == "adicionar_testes":
        validar_geracao_testes(
            analise
        )

    elif tipo == "configurar_build":
        validar_configuracao_build(
            analise
        )

    elif tipo == "organizar_estrutura":
        validar_organizacao_estrutura(
            analise
        )

    return True

def validar_configuracao_build(
    analise,
):
    """
    Verifica se é seguro adicionar um build
    Maven ao repositório.
    """

    java = analise.get(
        "java_backend",
        {},
    )

    stack = analise.get(
        "stack_java",
        {},
    )

    if not java.get("java"):
        raise RuntimeError(
            "Configuração de build bloqueada: "
            "nenhum código Java foi identificado."
        )

    if stack.get("build_tool"):
        raise RuntimeError(
            "Configuração de build bloqueada: "
            f"o projeto já utiliza "
            f"{stack['build_tool']}."
        )

    return True

def validar_organizacao_estrutura(
    analise,
):
    """
    Determina se a organização automática
    da estrutura Java é permitida.
    """

    java = analise.get(
        "java_backend",
        {},
    )

    if not java.get("java"):
        raise RuntimeError(
            "Organização bloqueada: "
            "nenhum código Java encontrado."
        )

    if java.get(
        "estrutura_java_padrao"
    ):
        raise RuntimeError(
            "Organização bloqueada: "
            "src/main/java já existe."
        )

    branch = analise[
        "branch_analise"
    ]

    arquivos = analise[
        "analise_branches"
    ]["branches"][branch]["arquivos"]

    movimentos = (
        planejar_movimentos_estrutura_maven(
            arquivos
        )
    )

    if not movimentos:
        raise RuntimeError(
            "Nenhum arquivo Java possui um "
            "movimento automático seguro."
        )

    return movimentos