
import json

import pytest

import app.permissions as permissions


REPO = "wjfo182/Estudos-Java"
OUTRO = "wjfo182/hello-world"


@pytest.fixture
def arquivo_isolado(tmp_path, monkeypatch):
    """
    Redireciona o arquivo de autorizações
    para um diretório temporário.

    Nunca altera a configuração real.
    """

    pasta = tmp_path / "config"
    arquivo = pasta / "authorized_repositories.json"

    monkeypatch.setattr(
        permissions,
        "CONFIG_DIR",
        pasta,
    )

    monkeypatch.setattr(
        permissions,
        "AUTHORIZED_FILE",
        arquivo,
    )

    return arquivo


def gravar_json(arquivo, dados):
    arquivo.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    arquivo.write_text(
        json.dumps(dados),
        encoding="utf-8",
    )


# 1. Instalação nova

def test_arquivo_ausente_nao_autoriza(
    arquivo_isolado,
):
    assert permissions.carregar_autorizados() == []

    assert permissions.repositorio_autorizado(
        REPO
    ) is False


# 2. Autorização explícita

def test_autorizacao_explicita(
    arquivo_isolado,
):
    permissions.autorizar_repositorio(REPO)

    assert permissions.repositorio_autorizado(
        REPO
    ) is True


# 3. Outro repositório não herda autorização

def test_autorizacao_nao_e_global(
    arquivo_isolado,
):
    permissions.autorizar_repositorio(REPO)

    assert permissions.repositorio_autorizado(
        OUTRO
    ) is False


# 4. Não duplica autorização

def test_autorizacao_nao_duplica(
    arquivo_isolado,
):
    permissions.autorizar_repositorio(REPO)
    permissions.autorizar_repositorio(REPO)

    assert permissions.carregar_autorizados() == [
        REPO
    ]


# 5. Revogação

def test_revogacao(
    arquivo_isolado,
):
    permissions.autorizar_repositorio(REPO)
    permissions.revogar_repositorio(REPO)

    assert permissions.repositorio_autorizado(
        REPO
    ) is False


# 6. JSON corrompido

def test_json_corrompido_bloqueia(
    arquivo_isolado,
):
    arquivo_isolado.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    arquivo_isolado.write_text(
        "{json invalido",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError):
        permissions.carregar_autorizados()


# 7. JSON com raiz incorreta

def test_json_raiz_incorreta(
    arquivo_isolado,
):
    gravar_json(arquivo_isolado, [REPO])

    with pytest.raises(RuntimeError):
        permissions.carregar_autorizados()


# 8. Campo obrigatório ausente

def test_campo_repositories_ausente(
    arquivo_isolado,
):
    gravar_json(arquivo_isolado, {})

    with pytest.raises(RuntimeError):
        permissions.carregar_autorizados()


# 9. String no lugar de lista

def test_string_nao_e_lista_autorizada(
    arquivo_isolado,
):
    gravar_json(
        arquivo_isolado,
        {"repositories": REPO},
    )

    with pytest.raises(RuntimeError):
        permissions.repositorio_autorizado(REPO)


# 10. Elemento com tipo inválido

def test_elemento_nao_string(
    arquivo_isolado,
):
    gravar_json(
        arquivo_isolado,
        {"repositories": [REPO, 123]},
    )

    with pytest.raises(RuntimeError):
        permissions.carregar_autorizados()


# 11. Nome inválido

def test_nome_repositorio_invalido(
    arquivo_isolado,
):
    gravar_json(
        arquivo_isolado,
        {"repositories": ["repositorio-sem-dono"]},
    )

    with pytest.raises(RuntimeError):
        permissions.carregar_autorizados()


# 12. Não sobrescrever configuração corrompida

def test_nao_sobrescreve_configuracao_invalida(
    arquivo_isolado,
):
    arquivo_isolado.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    conteudo = "{configuracao corrompida"

    arquivo_isolado.write_text(
        conteudo,
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError):
        permissions.autorizar_repositorio(REPO)

    assert arquivo_isolado.read_text(
        encoding="utf-8"
    ) == conteudo


# 13. Salvamento exige lista válida

def test_salvar_rejeita_tipo_invalido(
    arquivo_isolado,
):
    with pytest.raises(RuntimeError):
        permissions.salvar_autorizados(REPO)

    assert not arquivo_isolado.exists()
