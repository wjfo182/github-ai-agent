import json
import subprocess
import base64
from urllib.parse import quote

def listar_repositorios(limite=100):
    """
    Lista os repositórios acessíveis pela autenticação
    atual do GitHub CLI.

    Esta função realiza apenas leitura.
    """

    if not 1 <= limite <= 100:
        raise ValueError("O limite deve estar entre 1 e 100.")

    comando = [
        "gh",
        "repo",
        "list",
        "--limit",
        str(limite),
        "--json",
        "nameWithOwner,description,isPrivate,url",
    ]

    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

    except FileNotFoundError as erro:
        raise RuntimeError(
            "GitHub CLI não encontrado."
        ) from erro

    except subprocess.CalledProcessError as erro:
        mensagem = erro.stderr.strip()

        raise RuntimeError(
            f"Falha ao consultar o GitHub: {mensagem}"
        ) from erro

    except subprocess.TimeoutExpired as erro:
        raise RuntimeError(
            "A consulta ao GitHub excedeu o tempo limite."
        ) from erro

    return json.loads(resultado.stdout)

def obter_repositorio(nome_completo):
    """
    Obtém informações de um repositório específico.

    Exemplo:
        usuario/meu-projeto
    """

    if not nome_completo or "/" not in nome_completo:
        raise ValueError(
            "Informe o repositório no formato usuario/repositorio."
        )

    comando = [
        "gh",
        "repo",
        "view",
        nome_completo,
        "--json",
        (
            "nameWithOwner,description,isPrivate,url,"
            "defaultBranchRef,primaryLanguage,languages,"
            "repositoryTopics"
        ),
    ]

    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

    except FileNotFoundError as erro:
        raise RuntimeError(
            "GitHub CLI não encontrado."
        ) from erro

    except subprocess.CalledProcessError as erro:
        mensagem = erro.stderr.strip()

        raise RuntimeError(
            f"Falha ao consultar o repositório: {mensagem}"
        ) from erro

    except subprocess.TimeoutExpired as erro:
        raise RuntimeError(
            "A consulta excedeu o tempo limite."
        ) from erro

    return json.loads(resultado.stdout)

def listar_arquivos_repositorio(nome_completo, branch=None):
    """
    Lista os arquivos de um repositório.

    Se uma branch for informada, consulta essa branch.
    Caso contrário, utiliza HEAD.

    Operação somente de leitura.
    """

    if not nome_completo or "/" not in nome_completo:
        raise ValueError(
            "Informe o repositório no formato usuario/repositorio."
        )

    referencia = branch if branch else "HEAD"

    comando = [
        "gh",
        "api",
        f"repos/{nome_completo}/git/trees/{referencia}?recursive=1",
    ]

    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

    except FileNotFoundError as erro:
        raise RuntimeError(
            "GitHub CLI não encontrado."
        ) from erro

    except subprocess.CalledProcessError as erro:
        mensagem = erro.stderr.strip()

        raise RuntimeError(
            f"Falha ao consultar arquivos: {mensagem}"
        ) from erro

    except subprocess.TimeoutExpired as erro:
        raise RuntimeError(
            "A consulta dos arquivos excedeu o tempo limite."
        ) from erro

    dados = json.loads(resultado.stdout)

    return [
        item["path"]
        for item in dados.get("tree", [])
        if item.get("type") == "blob"
    ]

def listar_branches(nome_completo):
    """
    Lista as branches disponíveis em um repositório.

    Operação somente de leitura.
    """

    if not nome_completo or "/" not in nome_completo:
        raise ValueError(
            "Informe o repositório no formato usuario/repositorio."
        )

    comando = [
        "gh",
        "api",
        f"repos/{nome_completo}/branches",
    ]

    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

    except FileNotFoundError as erro:
        raise RuntimeError(
            "GitHub CLI não encontrado."
        ) from erro

    except subprocess.CalledProcessError as erro:
        mensagem = erro.stderr.strip()

        raise RuntimeError(
            f"Falha ao consultar branches: {mensagem}"
        ) from erro

    except subprocess.TimeoutExpired as erro:
        raise RuntimeError(
            "A consulta das branches excedeu o tempo limite."
        ) from erro

    dados = json.loads(resultado.stdout)

    return [
        branch["name"]
        for branch in dados
    ]

def obter_conteudo_arquivo(nome_completo, caminho, branch):
    """
    Obtém o conteúdo de um arquivo específico
    de uma determinada branch do repositório.

    Operação somente de leitura.
    """

    if not nome_completo or "/" not in nome_completo:
        raise ValueError(
            "Informe o repositório no formato usuario/repositorio."
        )

    if not caminho:
        raise ValueError(
            "Informe o caminho do arquivo."
        )

    if not branch:
        raise ValueError(
            "Informe a branch."
        )

    caminho_codificado = quote(
        caminho,
        safe="/",
    )

    branch_codificada = quote(
        branch,
        safe="",
    )

    comando = [
        "gh",
        "api",
        (
            f"repos/{nome_completo}/contents/"
            f"{caminho_codificado}"
            f"?ref={branch_codificada}"
        ),
    ]

    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

    except FileNotFoundError as erro:
        raise RuntimeError(
            "GitHub CLI não encontrado."
        ) from erro

    except subprocess.CalledProcessError as erro:
        mensagem = erro.stderr.strip()

        raise RuntimeError(
            f"Falha ao obter arquivo: {mensagem}"
        ) from erro

    except subprocess.TimeoutExpired as erro:
        raise RuntimeError(
            "A consulta do arquivo excedeu o tempo limite."
        ) from erro

    dados = json.loads(resultado.stdout)

    if dados.get("encoding") != "base64":
        raise RuntimeError(
            "Formato de conteúdo não suportado."
        )

    conteudo_base64 = dados.get("content", "")

    try:
        conteudo = base64.b64decode(
            conteudo_base64
        ).decode("utf-8")

    except (ValueError, UnicodeDecodeError) as erro:
        raise RuntimeError(
            "Não foi possível decodificar o arquivo."
        ) from erro

    return conteudo