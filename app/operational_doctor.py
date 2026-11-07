
import shutil
import subprocess

from app.doctor import Verificacao


def verificar_servicos(
    *,
    localizar_executavel=None,
    executar_comando=None,
):
    """
    Verifica se GitHub CLI e Ollama estão operacionais.

    Não executa comandos de escrita.
    Não modifica repositórios.
    Não realiza login nem instala programas.

    Permite substituir subprocess.run nos testes.
    """

    which = (
        localizar_executavel
        if localizar_executavel is not None
        else shutil.which
    )

    executar = (
        executar_comando
        if executar_comando is not None
        else subprocess.run
    )

    verificacoes = (
        (
            "GitHub: autenticação",
            "gh",
            [
                "gh",
                "auth",
                "status",
                "--hostname",
                "github.com",
            ],
        ),
        (
            "Ollama: serviço",
            "ollama",
            [
                "ollama",
                "list",
            ],
        ),
    )

    resultados = []

    for nome, executavel, comando in verificacoes:

        if not which(executavel):

            resultados.append(
                Verificacao(
                    nome,
                    "FALHA",
                    "Executável não encontrado.",
                )
            )

            continue

        try:

            processo = executar(
                comando,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
                check=False,
            )

        except subprocess.TimeoutExpired:

            resultados.append(
                Verificacao(
                    nome,
                    "FALHA",
                    "Tempo limite de 10 segundos excedido.",
                )
            )

            continue

        except OSError:

            resultados.append(
                Verificacao(
                    nome,
                    "FALHA",
                    "Não foi possível executar o comando.",
                )
            )

            continue

        if processo.returncode == 0:

            resultados.append(
                Verificacao(
                    nome,
                    "OK",
                    "Verificação operacional concluída.",
                )
            )

        else:

            resultados.append(
                Verificacao(
                    nome,
                    "FALHA",
                    "Comando retornou erro. "
                    "Verifique a autenticação ou o serviço.",
                )
            )

    return resultados
