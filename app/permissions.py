
import json
import re

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG_DIR = BASE_DIR / "config"

AUTHORIZED_FILE = (
    CONFIG_DIR / "authorized_repositories.json"
)


PADRAO_REPOSITORIO = re.compile(
    r"^[A-Za-z0-9-]+/[A-Za-z0-9_.-]+$"
)


def validar_lista_repositorios(repositorios):
    """
    Valida o formato da lista de autorizações.

    Esperado:
    [
        "usuario/repositorio",
        "organizacao/outro-repositorio"
    ]
    """

    if not isinstance(repositorios, list):
        raise RuntimeError(
            "A configuração de autorizações "
            "deve conter uma lista."
        )

    for nome in repositorios:

        if (
            not isinstance(nome, str)
            or not PADRAO_REPOSITORIO.fullmatch(nome)
        ):
            raise RuntimeError(
                "A configuração contém um nome "
                "de repositório inválido."
            )

    return repositorios


def carregar_autorizados():
    """
    Carrega as autorizações locais.

    Arquivo ausente:
        nenhuma autorização.

    Arquivo inválido:
        bloqueia a operação.
    """

    if not AUTHORIZED_FILE.exists():
        return []

    try:

        dados = json.loads(
            AUTHORIZED_FILE.read_text(
                encoding="utf-8"
            )
        )

    except (
        json.JSONDecodeError,
        OSError,
        UnicodeError,
    ) as erro:

        raise RuntimeError(
            "Não foi possível carregar os "
            "repositórios autorizados."
        ) from erro

    if not isinstance(dados, dict):
        raise RuntimeError(
            "Formato inválido do arquivo "
            "de autorizações."
        )

    if "repositories" not in dados:
        raise RuntimeError(
            "Campo 'repositories' ausente "
            "na configuração."
        )

    return validar_lista_repositorios(
        dados["repositories"]
    )


def salvar_autorizados(repositorios):
    """
    Salva somente listas válidas.
    """

    validar_lista_repositorios(
        repositorios
    )

    CONFIG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    dados = {
        "repositories": sorted(
            set(repositorios)
        )
    }

    AUTHORIZED_FILE.write_text(
        json.dumps(
            dados,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def repositorio_autorizado(nome_completo):
    """
    Verifica autorização explícita.

    Sem configuração, retorna False.
    Configuração inválida causa erro.
    """

    if not isinstance(nome_completo, str):
        return False

    return (
        nome_completo
        in carregar_autorizados()
    )


def autorizar_repositorio(nome_completo):
    """
    Registra uma autorização.

    A confirmação humana deve ocorrer
    no fluxo que chama esta função.
    """

    validar_lista_repositorios(
        [nome_completo]
    )

    repositorios = carregar_autorizados()

    if nome_completo not in repositorios:

        repositorios.append(
            nome_completo
        )

        salvar_autorizados(
            repositorios
        )


def revogar_repositorio(nome_completo):
    """
    Remove uma autorização existente.
    """

    repositorios = carregar_autorizados()

    repositorios = [
        repo
        for repo in repositorios
        if repo != nome_completo
    ]

    salvar_autorizados(
        repositorios
    )

def exigir_repositorio_autorizado(nome_completo):
    """
    Interrompe a operação quando o repositório
    não possui autorização explícita.

    Uma configuração ausente ou inválida
    nunca concede permissão.
    """

    if (
        not isinstance(nome_completo, str)
        or not PADRAO_REPOSITORIO.fullmatch(
            nome_completo
        )
    ):
        raise RuntimeError(
            "Nome de repositório inválido."
        )

    if not repositorio_autorizado(
        nome_completo
    ):
        raise RuntimeError(
            "Operação bloqueada: repositório "
            f"não autorizado: {nome_completo}"
        )

    return True
