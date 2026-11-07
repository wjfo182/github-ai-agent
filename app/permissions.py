import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"

AUTHORIZED_FILE = (
    CONFIG_DIR / "authorized_repositories.json"
)


def carregar_autorizados():
    """
    Retorna a lista de repositórios que o usuário
    autorizou o agente a manipular.
    """

    if not AUTHORIZED_FILE.exists():
        return []

    try:
        dados = json.loads(
            AUTHORIZED_FILE.read_text(
                encoding="utf-8"
            )
        )

    except (json.JSONDecodeError, OSError) as erro:
        raise RuntimeError(
            "Não foi possível carregar os "
            "repositórios autorizados."
        ) from erro

    return dados.get(
        "repositories",
        [],
    )

def salvar_autorizados(repositorios):
    """
    Salva a lista de repositórios autorizados.
    """

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
    return nome_completo in carregar_autorizados()

def autorizar_repositorio(nome_completo):
    """
    Adiciona um repositório à lista autorizada.
    """

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
    Remove um repositório da lista autorizada.
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