import re
from pathlib import PurePosixPath

from app.github_client import (
    obter_conteudo_arquivo,
)


ANOTACOES_HTTP = {
    "GetMapping": "GET",
    "PostMapping": "POST",
    "PutMapping": "PUT",
    "PatchMapping": "PATCH",
    "DeleteMapping": "DELETE",
    "RequestMapping": "REQUEST",
}


def extrair_package(conteudo):
    """
    Extrai o package declarado no arquivo Java.
    """

    padrao = r"^\s*package\s+([\w.]+)\s*;"

    resultado = re.search(
        padrao,
        conteudo,
        re.MULTILINE,
    )

    if resultado:
        return resultado.group(1)

    return None

def extrair_classe(conteudo):
    """
    Extrai o nome da primeira classe encontrada.
    """

    padrao = (
        r"\b(?:public\s+)?"
        r"(?:abstract\s+|final\s+)?"
        r"class\s+([A-Za-z_]\w*)"
    )

    resultado = re.search(
        padrao,
        conteudo,
    )

    if resultado:
        return resultado.group(1)

    return None

def extrair_anotacoes(conteudo):
    """
    Extrai anotações Java.

    Exemplos:
    @Service
    @RestController
    @GetMapping
    """

    padrao = r"@([A-Za-z_]\w*)"

    anotacoes = re.findall(
        padrao,
        conteudo,
    )

    return sorted(
        set(anotacoes)
    )

def extrair_metodos_publicos(conteudo):
    """
    Extrai métodos públicos simples.

    Não é um parser Java completo.
    """

    padrao = re.compile(
        r"""
        \bpublic
        \s+
        (?:static\s+)?
        (?:final\s+)?
        ([\w<>\[\],.?]+)
        \s+
        ([A-Za-z_]\w*)
        \s*
        \(
        ([^)]*)
        \)
        """,
        re.VERBOSE,
    )

    metodos = []

    for resultado in padrao.finditer(
        conteudo
    ):
        retorno = resultado.group(1)
        nome = resultado.group(2)
        parametros = resultado.group(3).strip()

        eh_main = (
            nome == "main"
            and "String" in parametros
        )

        metodos.append({
            "nome": nome,
            "retorno": retorno,
            "parametros": parametros,
            "eh_main": eh_main,
        })

    return metodos

def classificar_classe(anotacoes):
    """
    Tenta identificar o papel arquitetural
    da classe pelas anotações encontradas.
    """

    anotacoes = set(
        anotacoes
    )

    if (
        "RestController" in anotacoes
        or "Controller" in anotacoes
    ):
        return "controller"

    if "Service" in anotacoes:
        return "service"

    if "Repository" in anotacoes:
        return "repository"

    if "Entity" in anotacoes:
        return "entity"

    if (
        "SpringBootApplication"
        in anotacoes
    ):
        return "application"

    return "classe_java"

def detectar_metodos_http(anotacoes):
    """
    Identifica métodos HTTP representados
    pelas anotações Spring.
    """

    metodos = []

    for anotacao in anotacoes:
        metodo = ANOTACOES_HTTP.get(
            anotacao
        )

        if metodo:
            metodos.append(
                metodo
            )

    return sorted(
        set(metodos)
    )

def analisar_codigo_java(conteudo):
    """
    Produz uma representação estrutural
    simples de um arquivo Java.
    """

    anotacoes = extrair_anotacoes(
        conteudo
    )

    return {
        "package": extrair_package(
            conteudo
        ),
        "classe": extrair_classe(
            conteudo
        ),
        "anotacoes": anotacoes,
        "papel": classificar_classe(
            anotacoes
        ),
        "metodos_http": detectar_metodos_http(
            anotacoes
        ),
        "metodos_publicos": extrair_metodos_publicos(
            conteudo
        ),
    }

def analisar_arquivos_java_repositorio(
    nome_completo,
    branch,
    arquivos,
):
    """
    Lê os arquivos Java da branch e analisa
    sua estrutura.

    Operação somente de leitura.
    """

    resultado = []

    arquivos_java = [
        arquivo
        for arquivo in arquivos
        if arquivo.lower().endswith(".java")
    ]

    for caminho in arquivos_java:

        conteudo = obter_conteudo_arquivo(
            nome_completo,
            caminho,
            branch,
        )

        estrutura = analisar_codigo_java(
            conteudo
        )

        resultado.append({
            "arquivo": caminho,
            **estrutura,
        })

    return resultado

def resumir_arquitetura_java(
    estruturas,
):
    """
    Resume os papéis das classes Java
    encontrados no repositório.
    """

    resumo = {
        "controllers": [],
        "services": [],
        "repositories": [],
        "entities": [],
        "applications": [],
        "outras_classes": [],
    }

    for estrutura in estruturas:

        item = {
            "arquivo": estrutura.get(
                "arquivo"
            ),
            "classe": estrutura.get(
                "classe"
            ),
        }

        papel = estrutura.get(
            "papel"
        )

        if papel == "controller":
            resumo["controllers"].append(
                item
            )

        elif papel == "service":
            resumo["services"].append(
                item
            )

        elif papel == "repository":
            resumo["repositories"].append(
                item
            )

        elif papel == "entity":
            resumo["entities"].append(
                item
            )

        elif papel == "application":
            resumo["applications"].append(
                item
            )

        else:
            resumo["outras_classes"].append(
                item
            )

    return resumo

def sugerir_tipos_testes(estruturas):
    """
    Sugere categorias de testes com base
    no papel arquitetural das classes.

    Não gera código de teste.
    """

    sugestoes = []

    for estrutura in estruturas:

        classe = estrutura.get("classe")
        arquivo = estrutura.get("arquivo")
        papel = estrutura.get("papel")

        metodos = [
            metodo
            for metodo in estrutura.get(
                "metodos_publicos",
                [],
            )
            if not metodo.get("eh_main")
        ]

        # Classe contendo somente main não é,
        # por padrão, candidata a geração
        # automática de teste.
        if not metodos:
            continue

        if papel == "service":
            sugestoes.append({
                "classe": classe,
                "arquivo": arquivo,
                "tipo_teste": "unitario_service",
                "motivo": (
                    "Classe de serviço com métodos "
                    "públicos testáveis."
                ),
            })

        elif papel == "controller":
            sugestoes.append({
                "classe": classe,
                "arquivo": arquivo,
                "tipo_teste": "controller",
                "motivo": (
                    "Controller identificado com "
                    "métodos públicos."
                ),
            })

        elif papel == "repository":
            sugestoes.append({
                "classe": classe,
                "arquivo": arquivo,
                "tipo_teste": "persistencia",
                "motivo": (
                    "Repository identificado."
                ),
            })

        elif papel == "classe_java":
            sugestoes.append({
                "classe": classe,
                "arquivo": arquivo,
                "tipo_teste": "unitario",
                "motivo": (
                    "Classe Java comum com métodos "
                    "públicos testáveis."
                ),
            })

    return sugestoes

def calcular_caminho_teste(
    caminho_origem,
    nome_classe,
):
    """
    Calcula deterministicamente o caminho do teste.

    Exemplo:

    src/main/java/com/exemplo/ProdutoService.java

    vira:

    src/test/java/com/exemplo/ProdutoServiceTest.java

    A IA não escolhe esse caminho.
    """

    origem = PurePosixPath(
        caminho_origem
    )

    raiz_principal = PurePosixPath(
        "src/main/java"
    )

    try:
        relativo = origem.relative_to(
            raiz_principal
        )

    except ValueError as erro:
        raise ValueError(
            "O arquivo Java não está dentro "
            "de src/main/java."
        ) from erro

    destino = (
        PurePosixPath("src/test/java")
        / relativo.parent
        / f"{nome_classe}Test.java"
    )

    return str(destino)

def planejar_movimentos_estrutura_maven(
    arquivos,
):
    """
    Planeja somente movimentos Java simples
    da raiz src/ para src/main/java/.

    Exemplo:
    src/Main.java
    ->
    src/main/java/Main.java

    Não executa nenhuma alteração.
    """

    arquivos_existentes = set(
        arquivos
    )

    movimentos = []

    for caminho in arquivos:

        origem = PurePosixPath(
            caminho
        )

        # Nesta primeira implementação,
        # aceitamos somente:
        #
        # src/Arquivo.java
        #
        # Não movemos estruturas arbitrárias.
        if (
            len(origem.parts) != 2
            or origem.parts[0] != "src"
            or origem.suffix.lower() != ".java"
        ):
            continue

        destino = (
            PurePosixPath("src/main/java")
            / origem.name
        )

        destino_str = str(
            destino
        )

        if destino_str in arquivos_existentes:
            raise RuntimeError(
                "Não é possível organizar "
                f"'{caminho}': o destino "
                f"'{destino_str}' já existe."
            )

        movimentos.append({
            "origem": caminho,
            "destino": destino_str,
        })

    return movimentos