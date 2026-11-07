
import pytest

from app.git_manager import escrever_arquivo_local


def test_cria_arquivo_dentro_repositorio(tmp_path):
    destino = escrever_arquivo_local(
        tmp_path,
        "src/test/java/CalculadoraTest.java",
        "class CalculadoraTest {}",
    )

    assert destino.is_file()
    assert destino.read_text(
        encoding="utf-8"
    ) == "class CalculadoraTest {}"


@pytest.mark.parametrize(
    "caminho",
    [
        "../fora.txt",
        "/tmp/fora.txt",
        ".git/config",
        "C:/Users/outro.txt",
        "src\\arquivo.java",
    ],
)
def test_caminhos_perigosos_bloqueados(
    tmp_path,
    caminho,
):
    with pytest.raises(RuntimeError):
        escrever_arquivo_local(
            tmp_path,
            caminho,
            "conteudo",
        )


def test_nao_sobrescreve_sem_permissao(
    tmp_path,
):
    arquivo = tmp_path / "README.md"
    arquivo.write_text(
        "original",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError):
        escrever_arquivo_local(
            tmp_path,
            "README.md",
            "novo",
        )

    assert arquivo.read_text(
        encoding="utf-8"
    ) == "original"


def test_sobrescrita_exige_revisao(
    tmp_path,
):
    arquivo = tmp_path / "README.md"
    arquivo.write_text(
        "original",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError):
        escrever_arquivo_local(
            tmp_path,
            "README.md",
            "novo",
            sobrescrever=True,
        )


def test_arquivo_modificado_bloqueia(
    tmp_path,
):
    arquivo = tmp_path / "README.md"
    arquivo.write_text(
        "modificado",
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError,
        match="mudou",
    ):
        escrever_arquivo_local(
            tmp_path,
            "README.md",
            "novo",
            sobrescrever=True,
            conteudo_esperado="original",
        )

    assert arquivo.read_text(
        encoding="utf-8"
    ) == "modificado"


def test_sobrescrita_revisada_funciona(
    tmp_path,
):
    arquivo = tmp_path / "README.md"
    arquivo.write_text(
        "original",
        encoding="utf-8",
    )

    escrever_arquivo_local(
        tmp_path,
        "README.md",
        "novo",
        sobrescrever=True,
        conteudo_esperado="original",
    )

    assert arquivo.read_text(
        encoding="utf-8"
    ) == "novo"
