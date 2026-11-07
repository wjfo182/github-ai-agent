import xml.etree.ElementTree as ET
from pathlib import PurePosixPath

from app.github_client import (
    obter_repositorio,
    listar_branches,
    listar_arquivos_repositorio,
    obter_conteudo_arquivo,
)
from app.java_analyzer import (
    analisar_arquivos_java_repositorio,
    resumir_arquitetura_java,
    sugerir_tipos_testes,
)

def analisar_repositorio(repo):
    """
    Analisa informações básicas de um repositório
    pensando em sua apresentação como portfólio.
    """

    problemas = []
    pontos_positivos = []

    nome = repo.get("nameWithOwner", "Desconhecido")
    descricao = repo.get("description")
    privado = repo.get("isPrivate", False)

    linguagem_info = repo.get("primaryLanguage")
    linguagem = (
        linguagem_info.get("name")
        if linguagem_info
        else None
    )

    topicos_info = repo.get("repositoryTopics") or []
    topicos = [
        topico.get("name")
        for topico in topicos_info
        if topico.get("name")
    ]

    # Descrição
    if descricao:
        pontos_positivos.append(
            "O repositório possui descrição."
        )
    else:
        problemas.append(
            "O repositório não possui descrição."
        )

    # Linguagem
    if linguagem:
        pontos_positivos.append(
            f"Linguagem principal identificada: {linguagem}."
        )
    else:
        problemas.append(
            "Não foi possível identificar a linguagem principal."
        )

    # Tópicos
    if topicos:
        pontos_positivos.append(
            f"Possui tópicos: {', '.join(topicos)}."
        )
    else:
        problemas.append(
            "O repositório não possui tópicos."
        )

    # Visibilidade
    if privado:
        problemas.append(
            "O repositório é privado e não pode ser visto "
            "publicamente no portfólio."
        )
    else:
        pontos_positivos.append(
            "O repositório é público."
        )

    return {
        "nome": nome,
        "linguagem": linguagem,
        "pontos_positivos": pontos_positivos,
        "problemas": problemas,
    }

EXTENSOES_LINGUAGENS = {
    ".java": "Java",
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".go": "Go",
    ".rb": "Ruby",
    ".php": "PHP",
}

def detectar_linguagens(arquivos):
    """
    Detecta linguagens de programação através
    das extensões dos arquivos encontrados.
    """

    linguagens = set()

    for arquivo in arquivos:
        extensao = PurePosixPath(arquivo).suffix.lower()

        linguagem = EXTENSOES_LINGUAGENS.get(extensao)

        if linguagem:
            linguagens.add(linguagem)

    return sorted(linguagens)

def analisar_branches(nome_completo, branch_padrao):
    """
    Analisa os arquivos e linguagens encontrados
    em cada branch do repositório.
    """

    branches = listar_branches(nome_completo)

    resultado = {
        "branch_padrao": branch_padrao,
        "branches": {},
        "alertas": [],
    }

    for branch in branches:
        arquivos = listar_arquivos_repositorio(
            nome_completo,
            branch,
        )

        linguagens = detectar_linguagens(arquivos)

        possui_readme = any(
            arquivo.lower() == "readme.md"
            for arquivo in arquivos
        )

        resultado["branches"][branch] = {
            "arquivos": arquivos,
            "linguagens": linguagens,
            "possui_readme": possui_readme,
        }
        dados_branch_padrao = resultado["branches"].get(
        branch_padrao,
        {}
    )

    linguagens_padrao = dados_branch_padrao.get(
        "linguagens",
        [],
    )

    if not linguagens_padrao:
        for branch, dados in resultado["branches"].items():

            if branch == branch_padrao:
                continue

            if dados["linguagens"]:
                resultado["alertas"].append(
                    f"A branch padrão '{branch_padrao}' "
                    f"não possui linguagem identificada, "
                    f"mas a branch '{branch}' contém: "
                    f"{', '.join(dados['linguagens'])}."
                )

    return resultado

    return resultado

def analisar_portfolio_repositorio(nome_completo):
    """
    Executa uma análise geral do repositório
    pensando em sua utilização como portfólio.
    """

    # 1. Obtém informações gerais do repositório
    repo = obter_repositorio(nome_completo)

    # 2. Descobre a branch padrão
    branch_info = repo.get("defaultBranchRef")

    branch_padrao = (
        branch_info.get("name")
        if branch_info
        else None
    )

    if not branch_padrao:
        raise RuntimeError(
            "Não foi possível identificar a branch padrão."
        )

    # 3. Faz análise básica
    analise_basica = analisar_repositorio(repo)

    # 4. Analisa todas as branches
    analise_branches = analisar_branches(
        nome_completo,
        branch_padrao,
    )

    # 5. Escolhe a melhor branch para analisar código
    branch_analise = selecionar_branch_para_analise(
        analise_branches
    )

    # 6. Obtém os arquivos da branch escolhida
    arquivos_branch = analise_branches["branches"][
        branch_analise
    ]["arquivos"]

    # 7. Analisa estrutura Java Backend
    analise_java = analisar_java_backend(
        arquivos_branch
    )

    # 8. Analisa Maven/Gradle e tecnologias
    stack_java = analisar_stack_java(
        nome_completo,
        branch_analise,
        arquivos_branch,
    )

    # 9. Analisa o conteúdo dos arquivos Java
    estrutura_codigo_java = analisar_arquivos_java_repositorio(
        nome_completo,
        branch_analise,
        arquivos_branch,
    )

    # 10. Resume a arquitetura Java encontrada
    arquitetura_java = resumir_arquitetura_java(
        estrutura_codigo_java
    )

    # 11. Identifica os tipos de teste apropriados para as classes encontradas
    sugestoes_testes = sugerir_tipos_testes(
        estrutura_codigo_java
)
    
    # 12. Analisa elegibilidade para testes automatizados
    elegibilidade_testes = analisar_elegibilidade_testes(
        arquivos_branch,
        analise_java,
        stack_java,
        estrutura_codigo_java,
    )

    # 13. Calcula a pontuação
    pontuacao = calcular_pontuacao_portfolio(
        repo,
        analise_java,
        stack_java,
        analise_branches,
        branch_analise,
    )

    # 14. Gera recomendações
    recomendacoes = gerar_recomendacoes_portfolio(
        repo,
        analise_branches,
        branch_analise,
        analise_java,
        stack_java,
    )

    # 15. Retorna toda a análise
    return {
    "repositorio": nome_completo,
    "dados_repositorio": repo,
    "analise_basica": analise_basica,
    "analise_branches": analise_branches,
    "branch_analise": branch_analise,
    "java_backend": analise_java,
    "stack_java": stack_java,
    "estrutura_codigo_java": estrutura_codigo_java,
    "arquitetura_java": arquitetura_java,
    "sugestoes_testes": sugestoes_testes,
    "elegibilidade_testes": elegibilidade_testes,
    "pontuacao": pontuacao,
    "recomendacoes": recomendacoes,
}

def selecionar_branch_para_analise(analise_branches):
    """
    Escolhe a branch mais adequada para análise de código.

    Prioriza a branch padrão quando ela contém código.
    Caso contrário, escolhe a branch com mais arquivos
    de linguagens reconhecidas.
    """

    branch_padrao = analise_branches["branch_padrao"]
    branches = analise_branches["branches"]

    dados_padrao = branches.get(branch_padrao, {})

    if dados_padrao.get("linguagens"):
        return branch_padrao

    melhor_branch = None
    maior_quantidade_codigo = 0

    for nome_branch, dados in branches.items():
        quantidade_codigo = 0

        for arquivo in dados["arquivos"]:
            extensao = PurePosixPath(arquivo).suffix.lower()

            if extensao in EXTENSOES_LINGUAGENS:
                quantidade_codigo += 1

        if quantidade_codigo > maior_quantidade_codigo:
            maior_quantidade_codigo = quantidade_codigo
            melhor_branch = nome_branch

    return melhor_branch or branch_padrao

def analisar_java_backend(arquivos):
    """
    Procura indicadores comuns de projetos Java Backend.
    """

    arquivos_normalizados = {
        arquivo.lower()
        for arquivo in arquivos
    }

    resultado = {
        "java": False,
        "build_tool": None,
        "estrutura_java_padrao": False,
        "testes": False,
        "readme": False,
        "gitignore": False,
        "docker": False,
        "configuracao_aplicacao": False,
        "recursos": False,
    }

    # Java
    resultado["java"] = any(
        arquivo.endswith(".java")
        for arquivo in arquivos_normalizados
    )

    # Maven
    if "pom.xml" in arquivos_normalizados:
        resultado["build_tool"] = "Maven"

    # Gradle
    elif (
        "build.gradle" in arquivos_normalizados
        or "build.gradle.kts" in arquivos_normalizados
    ):
        resultado["build_tool"] = "Gradle"

    # Estrutura padrão
    resultado["estrutura_java_padrao"] = any(
        arquivo.startswith("src/main/java/")
        for arquivo in arquivos_normalizados
    )

    # Testes
    resultado["testes"] = any(
        arquivo.startswith("src/test/java/")
        for arquivo in arquivos_normalizados
    )

    # README
    resultado["readme"] = (
        "readme.md" in arquivos_normalizados
    )

    # .gitignore
    resultado["gitignore"] = (
        ".gitignore" in arquivos_normalizados
    )

    # Docker
    resultado["docker"] = any(
        arquivo in {
            "dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
        }
        for arquivo in arquivos_normalizados
    )

    # Recursos Java
    resultado["recursos"] = any(
        arquivo.startswith("src/main/resources/")
        for arquivo in arquivos_normalizados
    )

    # Configuração típica de aplicações Java/Spring
    resultado["configuracao_aplicacao"] = any(
        arquivo in {
            "src/main/resources/application.properties",
            "src/main/resources/application.yml",
            "src/main/resources/application.yaml",
        }
        for arquivo in arquivos_normalizados
    )

    return resultado

def localizar_arquivo_build(arquivos):
    """
    Localiza o arquivo de build principal do projeto Java.

    Prioridade:
    1. pom.xml
    2. build.gradle
    3. build.gradle.kts
    """

    nomes = {
        arquivo.lower(): arquivo
        for arquivo in arquivos
    }

    if "pom.xml" in nomes:
        return {
            "tipo": "Maven",
            "arquivo": nomes["pom.xml"],
        }

    if "build.gradle" in nomes:
        return {
            "tipo": "Gradle",
            "arquivo": nomes["build.gradle"],
        }

    if "build.gradle.kts" in nomes:
        return {
            "tipo": "Gradle",
            "arquivo": nomes["build.gradle.kts"],
        }

    return None

def analisar_pom(conteudo):
    """
    Analisa um pom.xml e identifica tecnologias
    comuns em projetos Java Backend.
    """

    resultado = {
        "spring_boot": False,
        "spring_web": False,
        "spring_data_jpa": False,
        "spring_security": False,
        "validation": False,
        "postgresql": False,
        "mysql": False,
        "h2": False,
        "lombok": False,
        "testes_spring": False,
        "swagger_openapi": False,
        "flyway": False,
        "liquibase": False,
        "dependencias": [],
    }

    try:
        raiz = ET.fromstring(conteudo)

    except ET.ParseError:
        raise RuntimeError(
            "O pom.xml não pôde ser interpretado como XML."
        )

    dependencias = []

    for dependencia in raiz.findall(".//{*}dependency"):

        artifact = dependencia.find("{*}artifactId")

        if artifact is None or not artifact.text:
            continue

        artifact_id = artifact.text.strip()

        dependencias.append(artifact_id)

    resultado["dependencias"] = sorted(
        set(dependencias)
    )

    conteudo_lower = conteudo.lower()

    resultado["spring_boot"] = (
        "spring-boot" in conteudo_lower
    )

    resultado["spring_web"] = (
        "spring-boot-starter-web" in dependencias
        or "spring-boot-starter-webflux" in dependencias
    )

    resultado["spring_data_jpa"] = (
        "spring-boot-starter-data-jpa"
        in dependencias
    )

    resultado["spring_security"] = (
        "spring-boot-starter-security"
        in dependencias
    )

    resultado["validation"] = (
        "spring-boot-starter-validation"
        in dependencias
    )

    resultado["postgresql"] = (
        "postgresql" in dependencias
    )

    resultado["mysql"] = (
        "mysql-connector-j" in dependencias
        or "mysql-connector-java" in dependencias
    )

    resultado["h2"] = (
        "h2" in dependencias
    )

    resultado["lombok"] = (
        "lombok" in dependencias
    )

    resultado["testes_spring"] = (
        "spring-boot-starter-test"
        in dependencias
    )

    resultado["swagger_openapi"] = any(
        "springdoc" in dependencia.lower()
        or "swagger" in dependencia.lower()
        for dependencia in dependencias
    )

    resultado["flyway"] = (
        "flyway-core" in dependencias
    )

    resultado["liquibase"] = (
        "liquibase-core" in dependencias
    )

    return resultado

def analisar_gradle(conteudo):
    """
    Analisa build.gradle ou build.gradle.kts
    procurando tecnologias comuns de Java Backend.
    """

    texto = conteudo.lower()

    return {
        "spring_boot": (
            "org.springframework.boot" in texto
        ),

        "spring_web": (
            "spring-boot-starter-web" in texto
            or "spring-boot-starter-webflux" in texto
        ),

        "spring_data_jpa": (
            "spring-boot-starter-data-jpa" in texto
        ),

        "spring_security": (
            "spring-boot-starter-security" in texto
        ),

        "validation": (
            "spring-boot-starter-validation" in texto
        ),

        "postgresql": (
            "org.postgresql" in texto
            or "postgresql" in texto
        ),

        "mysql": (
            "mysql-connector" in texto
        ),

        "h2": (
            "com.h2database" in texto
        ),

        "lombok": (
            "lombok" in texto
        ),

        "testes_spring": (
            "spring-boot-starter-test" in texto
        ),

        "swagger_openapi": (
            "springdoc" in texto
            or "swagger" in texto
        ),

        "flyway": (
            "flyway" in texto
        ),

        "liquibase": (
            "liquibase" in texto
        ),
    }

def analisar_stack_java(
    nome_completo,
    branch,
    arquivos,
):
    """
    Analisa o arquivo de build do projeto
    para identificar a stack Java Backend.
    """

    build = localizar_arquivo_build(arquivos)

    if not build:
        return {
            "build_tool": None,
            "build_file": None,
            "tecnologias": None,
        }

    conteudo = obter_conteudo_arquivo(
        nome_completo,
        build["arquivo"],
        branch,
    )

    if build["tipo"] == "Maven":
        tecnologias = analisar_pom(conteudo)

    else:
        tecnologias = analisar_gradle(conteudo)

    return {
        "build_tool": build["tipo"],
        "build_file": build["arquivo"],
        "tecnologias": tecnologias,
    }

def calcular_pontuacao_portfolio(
    repo,
    java_backend,
    stack_java,
    analise_branches,
    branch_analise,
):
    """
    Calcula um índice de prontidão do repositório
    para um portfólio Java Backend.

    Pontuação máxima: 100.
    """

    pontuacao = 0
    criterios = []

    tecnologias = stack_java.get("tecnologias") or {}

    dados_branch = analise_branches["branches"].get(
        branch_analise,
        {},
    )

    # Código Java - 10
    if java_backend.get("java"):
        pontuacao += 10
        criterios.append(
            ("Código Java", 10, True)
        )
    else:
        criterios.append(
            ("Código Java", 10, False)
        )

    # Repositório público - 10
    if not repo.get("isPrivate", True):
        pontuacao += 10
        criterios.append(
            ("Repositório público", 10, True)
        )
    else:
        criterios.append(
            ("Repositório público", 10, False)
        )

    # Descrição - 10
    if repo.get("description"):
        pontuacao += 10
        criterios.append(
            ("Descrição do projeto", 10, True)
        )
    else:
        criterios.append(
            ("Descrição do projeto", 10, False)
        )

    # README - 10
    if dados_branch.get("possui_readme"):
        pontuacao += 10
        criterios.append(
            ("README na branch analisada", 10, True)
        )
    else:
        criterios.append(
            ("README na branch analisada", 10, False)
        )

    # Build - 10
    if stack_java.get("build_tool"):
        pontuacao += 10
        criterios.append(
            ("Maven ou Gradle", 10, True)
        )
    else:
        criterios.append(
            ("Maven ou Gradle", 10, False)
        )

    # Estrutura Java - 10
    if java_backend.get("estrutura_java_padrao"):
        pontuacao += 10
        criterios.append(
            ("Estrutura src/main/java", 10, True)
        )
    else:
        criterios.append(
            ("Estrutura src/main/java", 10, False)
        )

    # Testes - 10
    if java_backend.get("testes"):
        pontuacao += 10
        criterios.append(
            ("Testes", 10, True)
        )
    else:
        criterios.append(
            ("Testes", 10, False)
        )

    # Spring Boot - 10
    if tecnologias.get("spring_boot"):
        pontuacao += 10
        criterios.append(
            ("Spring Boot", 10, True)
        )
    else:
        criterios.append(
            ("Spring Boot", 10, False)
        )

    # Spring Web - 10
    if tecnologias.get("spring_web"):
        pontuacao += 10
        criterios.append(
            ("Spring Web", 10, True)
        )
    else:
        criterios.append(
            ("Spring Web", 10, False)
        )

    # Persistência/banco - 5
    possui_banco = (
        tecnologias.get("postgresql")
        or tecnologias.get("mysql")
        or tecnologias.get("h2")
        or tecnologias.get("spring_data_jpa")
    )

    if possui_banco:
        pontuacao += 5
        criterios.append(
            ("Persistência / banco", 5, True)
        )
    else:
        criterios.append(
            ("Persistência / banco", 5, False)
        )

    # Docker - 5
    if java_backend.get("docker"):
        pontuacao += 5
        criterios.append(
            ("Docker", 5, True)
        )
    else:
        criterios.append(
            ("Docker", 5, False)
        )

    if pontuacao >= 80:
        nivel = "Forte para portfólio"

    elif pontuacao >= 60:
        nivel = "Bom, mas pode melhorar"

    elif pontuacao >= 40:
        nivel = "Em desenvolvimento"

    else:
        nivel = "Inicial"

    return {
        "pontuacao": pontuacao,
        "maximo": 100,
        "nivel": nivel,
        "criterios": criterios,
    }

def gerar_recomendacoes_portfolio(
    repo,
    analise_branches,
    branch_analise,
    java_backend,
    stack_java,
):
    """
    Gera recomendações priorizadas para melhorar
    a apresentação do repositório no portfólio.
    """

    recomendacoes = []

    branch_padrao = analise_branches["branch_padrao"]

    dados_branch = analise_branches["branches"].get(
        branch_analise,
        {},
    )

    tecnologias = stack_java.get("tecnologias") or {}

    # 1. Código fora da branch padrão
    if branch_analise != branch_padrao:
        recomendacoes.append({
            "prioridade": "ALTA",
            "titulo": "Organizar as branches",
            "motivo": (
                f"O código principal está na branch "
                f"'{branch_analise}', enquanto a branch "
                f"padrão é '{branch_padrao}'."
            ),
            "acao": (
                "Avaliar a consolidação do código na "
                "branch principal antes de apresentar "
                "o projeto no portfólio."
            ),
        })

    # 2. Repositório privado
    if repo.get("isPrivate", True):
        recomendacoes.append({
            "prioridade": "ALTA",
            "titulo": "Revisar a visibilidade",
            "motivo": (
                "O repositório está privado e não poderá "
                "ser acessado por recrutadores."
            ),
            "acao": (
                "Quando o projeto estiver pronto para "
                "portfólio, avaliar torná-lo público."
            ),
        })

    # 3. README
    if not dados_branch.get("possui_readme"):
        recomendacoes.append({
            "prioridade": "ALTA",
            "titulo": "Adicionar README ao projeto",
            "motivo": (
                "A branch que contém o código não possui "
                "README.md."
            ),
            "acao": (
                "Criar um README explicando objetivo, "
                "tecnologias, estrutura e como executar."
            ),
        })

    # 4. Descrição
    if not repo.get("description"):
        recomendacoes.append({
            "prioridade": "MÉDIA",
            "titulo": "Adicionar descrição",
            "motivo": (
                "O repositório não possui uma descrição clara."
            ),
            "acao": (
                "Adicionar uma descrição curta dizendo "
                "o objetivo e as principais tecnologias."
            ),
        })

    # 5. Tópicos
    if not repo.get("repositoryTopics"):
        recomendacoes.append({
            "prioridade": "MÉDIA",
            "titulo": "Adicionar tópicos ao GitHub",
            "motivo": (
                "O repositório não possui topics."
            ),
            "acao": (
                "Adicionar tópicos como java, backend, "
                "spring-boot ou outros que realmente "
                "representem o projeto."
            ),
        })

    # 6. Build tool
    if (
        java_backend.get("java")
        and not stack_java.get("build_tool")
    ):
        recomendacoes.append({
            "prioridade": "MÉDIA",
            "titulo": "Avaliar Maven ou Gradle",
            "motivo": (
                "Há código Java, mas não foi encontrado "
                "pom.xml ou build.gradle."
            ),
            "acao": (
                "Se este repositório evoluir para um projeto "
                "Java Backend completo, considerar Maven "
                "ou Gradle para dependências e build."
            ),
        })

    # 7. Estrutura Java padrão
    if (
        java_backend.get("java")
        and not java_backend.get("estrutura_java_padrao")
    ):
        recomendacoes.append({
            "prioridade": "MÉDIA",
            "titulo": "Revisar estrutura do projeto Java",
            "motivo": (
                "Não foi encontrada a estrutura "
                "src/main/java."
            ),
            "acao": (
                "Para projetos Java estruturados, avaliar "
                "a organização src/main/java e "
                "src/test/java."
            ),
        })

    # 8. Testes
    if (
        stack_java.get("build_tool")
        and not java_backend.get("testes")
    ):
        recomendacoes.append({
            "prioridade": "MÉDIA",
            "titulo": "Adicionar testes",
            "motivo": (
                "O projeto utiliza uma ferramenta de build, "
                "mas não foi encontrada estrutura de testes."
            ),
            "acao": (
                "Adicionar testes automatizados relevantes "
                "para demonstrar qualidade do projeto."
            ),
        })

    # 9. Spring Boot encontrado, mas sem Web
    if (
        tecnologias.get("spring_boot")
        and not tecnologias.get("spring_web")
    ):
        recomendacoes.append({
            "prioridade": "BAIXA",
            "titulo": "Verificar camada Web",
            "motivo": (
                "Spring Boot foi encontrado, mas "
                "Spring Web não foi identificado."
            ),
            "acao": (
                "Se o projeto for uma API REST, verificar "
                "se a dependência Web está configurada."
            ),
        })

    # 10. Docker
    if (
        tecnologias.get("spring_boot")
        and not java_backend.get("docker")
    ):
        recomendacoes.append({
            "prioridade": "BAIXA",
            "titulo": "Avaliar Docker",
            "motivo": (
                "O projeto utiliza Spring Boot, mas não "
                "possui configuração Docker detectada."
            ),
            "acao": (
                "Docker pode ser adicionado posteriormente "
                "para facilitar execução e demonstração."
            ),
        })

    ordem = {
        "ALTA": 0,
        "MÉDIA": 1,
        "BAIXA": 2,
    }

    recomendacoes.sort(
        key=lambda item: ordem[item["prioridade"]]
    )

    return recomendacoes

def criar_proposta_readme(
    nome_completo,
    branch_analise,
):
    """
    Cria uma proposta de ação para adicionar
    um README ao projeto.

    Esta função não modifica nenhum arquivo.
    """

    return {
        "tipo": "criar_readme",
        "titulo": "Criar README.md",
        "repositorio": nome_completo,
        "branch": branch_analise,
        "detalhes": [
            f"Criar README.md para {nome_completo}.",
            (
                f"Usar a branch '{branch_analise}' "
                "como referência para o conteúdo."
            ),
            "A alteração será feita somente localmente.",
            "Nenhum commit será enviado ao GitHub.",
            "Nenhum push será executado.",
        ],
    }

def detectar_framework_testes(stack_java):
    """
    Identifica o framework de testes disponível
    com base nas dependências detectadas no build.
    """

    tecnologias = (
        stack_java.get("tecnologias")
        or {}
    )

    # Spring Boot Starter Test já inclui
    # infraestrutura de testes baseada em JUnit.
    if tecnologias.get("testes_spring"):
        return "Spring Boot Test"

    dependencias = tecnologias.get(
        "dependencias",
        [],
    )

    texto_dependencias = " ".join(
        str(dependencia)
        for dependencia in dependencias
    ).lower()

    if "junit" in texto_dependencias:
        return "JUnit"

    return None

def analisar_elegibilidade_testes(
    arquivos,
    java_backend,
    stack_java,
    estrutura_codigo_java,
):
    """
    Avalia se o projeto possui estrutura suficiente
    para receber testes automatizados de forma segura.

    Esta função não cria testes.
    """

    arquivos_java = [
        arquivo
        for arquivo in arquivos
        if arquivo.lower().endswith(".java")
    ]

    motivos_bloqueio = []
    pontos_favoraveis = []

    # -------------------------------------------------
    # Java
    # -------------------------------------------------

    if java_backend.get("java"):
        pontos_favoraveis.append(
            "Código Java encontrado."
        )
    else:
        motivos_bloqueio.append(
            "Nenhum código Java foi encontrado."
        )

    # -------------------------------------------------
    # Build tool
    # -------------------------------------------------

    build_tool = stack_java.get(
        "build_tool"
    )

    if build_tool:
        pontos_favoraveis.append(
            f"Ferramenta de build identificada: "
            f"{build_tool}."
        )
    else:
        motivos_bloqueio.append(
            "Maven ou Gradle não foi identificado."
        )

    # -------------------------------------------------
    # Estrutura Java padrão
    # -------------------------------------------------

    if java_backend.get(
        "estrutura_java_padrao"
    ):
        pontos_favoraveis.append(
            "Estrutura src/main/java encontrada."
        )
    else:
        motivos_bloqueio.append(
            "Estrutura src/main/java não encontrada."
        )

    # -------------------------------------------------
    # Framework de testes
    # -------------------------------------------------

    framework_testes = detectar_framework_testes(
        stack_java
    )

    if framework_testes:
        pontos_favoraveis.append(
            f"Framework de testes identificado: "
            f"{framework_testes}."
        )
    else:
        motivos_bloqueio.append(
            "Nenhum framework de testes "
            "compatível foi identificado."
        )

    # -------------------------------------------------
    # Testes existentes
    # -------------------------------------------------

    possui_testes = java_backend.get(
        "testes",
        False,
    )

    if possui_testes:
        pontos_favoraveis.append(
            "Estrutura de testes já existente."
        )

    # -------------------------------------------------
    # Métodos candidatos a testes
    # -------------------------------------------------

    metodos_testaveis = []

    for classe in estrutura_codigo_java:

        for metodo in classe.get(
            "metodos_publicos",
            [],
        ):

            # Não considerar o método main como
            # candidato automático a teste unitário.
            if metodo.get("eh_main"):
                continue

            metodos_testaveis.append({
                "classe": classe.get(
                    "classe"
                ),
                "arquivo": classe.get(
                    "arquivo"
                ),
                "metodo": metodo.get(
                    "nome"
                ),
            })

    if metodos_testaveis:
        pontos_favoraveis.append(
            "Métodos públicos candidatos "
            "a testes foram encontrados."
        )
    else:
        motivos_bloqueio.append(
            "Nenhum método público apropriado "
            "para teste foi identificado."
        )

    # -------------------------------------------------
    # Elegibilidade final
    # -------------------------------------------------

    elegivel = (
        java_backend.get("java")
        and bool(build_tool)
        and java_backend.get(
            "estrutura_java_padrao"
        )
        and bool(framework_testes)
        and bool(metodos_testaveis)
    )

    return {
        "elegivel": elegivel,
        "build_tool": build_tool,
        "framework_testes": framework_testes,
        "possui_testes": possui_testes,
        "quantidade_arquivos_java": len(
            arquivos_java
        ),
        "arquivos_java": arquivos_java,
        "metodos_testaveis": metodos_testaveis,
        "pontos_favoraveis": pontos_favoraveis,
        "motivos_bloqueio": motivos_bloqueio,
    }