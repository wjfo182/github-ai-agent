
"""
Informações de versão do GitHub AI Agent.

Este arquivo centraliza o número da versão
para evitar inconsistências entre módulos.
"""

VERSION = (1, 0, 0)

__version__ = ".".join(
    str(parte) for parte in VERSION
)


def obter_versao():
    """Retorna a versão atual do aplicativo."""
    return __version__


def main():
    print(f"GitHub AI Agent v{obter_versao()}")


if __name__ == "__main__":
    main()
