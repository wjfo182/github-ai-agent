
import re

from app.version import VERSION, __version__, obter_versao


def test_versao_atual():
    assert obter_versao() == "1.0.0"


def test_versao_e_tupla_consistentes():
    esperado = ".".join(
        str(parte) for parte in VERSION
    )

    assert __version__ == esperado


def test_versao_utiliza_formato_semantico():
    assert re.fullmatch(
        r"\d+\.\d+\.\d+",
        __version__,
    )
