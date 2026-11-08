
import subprocess

import pytest

from app.git_manager import validar_destino_origin


REPO = "wjfo182/Estudos-Java"


def git(repo, *argumentos):
    resultado = subprocess.run(
        ["git", "-C", str(repo), *argumentos],
        capture_output=True,
        text=True,
        check=True,
    )

    return resultado.stdout.strip()


@pytest.fixture
def repo_local(tmp_path):
    git(tmp_path, "init", "-q")
    return tmp_path


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/wjfo182/Estudos-Java.git",
        "git@github.com:wjfo182/Estudos-Java.git",
        "ssh://git@github.com/wjfo182/Estudos-Java.git",
    ],
)
def test_urls_validas(repo_local, url):
    git(
        repo_local,
        "remote",
        "add",
        "origin",
        url,
    )

    assert validar_destino_origin(
        repo_local,
        REPO,
    ) is True


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/outro/projeto.git",
        "https://github.com.evil.com/wjfo182/Estudos-Java.git",
        "https://github.com/wjfo182/Estudos-Java/extra",
        "file:///tmp/repositorio.git",
    ],
)
def test_urls_incorretas_bloqueadas(
    repo_local,
    url,
):
    git(
        repo_local,
        "remote",
        "add",
        "origin",
        url,
    )

    with pytest.raises(RuntimeError):
        validar_destino_origin(
            repo_local,
            REPO,
        )


def test_pushurl_diferente_bloqueada(
    repo_local,
):
    git(
        repo_local,
        "remote",
        "add",
        "origin",
        "https://github.com/wjfo182/Estudos-Java.git",
    )

    git(
        repo_local,
        "remote",
        "set-url",
        "--push",
        "origin",
        "https://github.com/outro/projeto.git",
    )

    with pytest.raises(RuntimeError):
        validar_destino_origin(
            repo_local,
            REPO,
        )


def test_multiplos_pushurls_bloqueados(
    repo_local,
):
    git(
        repo_local,
        "remote",
        "add",
        "origin",
        "https://github.com/wjfo182/Estudos-Java.git",
    )

    for url in (
        "https://github.com/wjfo182/Estudos-Java.git",
        "https://github.com/outro/projeto.git",
    ):
        git(
            repo_local,
            "remote",
            "set-url",
            "--push",
            "--add",
            "origin",
            url,
        )

    with pytest.raises(RuntimeError):
        validar_destino_origin(
            repo_local,
            REPO,
        )


def test_origin_ausente_bloqueado(
    repo_local,
):
    with pytest.raises(RuntimeError):
        validar_destino_origin(
            repo_local,
            REPO,
        )
