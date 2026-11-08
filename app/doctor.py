
import importlib.util
import json
import shutil

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Verificacao:
    nome: str
    status: str
    detalhe: str


ARQUIVOS_ESSENCIAIS = (
    "app/main.py",
    "app/security.py",
    "app/ai_dispatcher.py",
    "app/git_manager.py",
    "app/commit_actions.py",
    "app/planner.py",
)


def verificar_prontidao(
    raiz_projeto=None,
    *,
    localizar_executavel=None,
    localizar_modulo=None,
):
    """
    Inspeciona requisitos locais do agente.

    Não executa comandos externos.
    Não acessa GitHub ou Ollama.
    Não modifica arquivos.

    As funções injetáveis permitem criar
    testes independentes do computador real.
    """

    raiz = (
        Path(raiz_projeto).resolve()
        if raiz_projeto is not None
        else Path(__file__).resolve().parent.parent
    )

    which = (
        localizar_executavel
        if localizar_executavel is not None
        else shutil.which
    )

    find_spec = (
        localizar_modulo
        if localizar_modulo is not None
        else importlib.util.find_spec
    )

    resultados = []

    def registrar(nome, status, detalhe):
        resultados.append(
            Verificacao(nome, status, detalhe)
        )

    # ------------------------------------------
    # 1. Executáveis essenciais
    # ------------------------------------------

    for comando in ("git", "gh", "ollama"):

        if which(comando):
            registrar(
                comando,
                "OK",
                "Executável encontrado.",
            )
        else:
            registrar(
                comando,
                "FALHA",
                "Executável não encontrado no PATH.",
            )

    # ------------------------------------------
    # 2. Bibliotecas Python
    # ------------------------------------------

    for modulo in ("pydantic", "ollama"):

        if find_spec(modulo) is not None:
            registrar(
                f"Python: {modulo}",
                "OK",
                "Módulo disponível.",
            )
        else:
            registrar(
                f"Python: {modulo}",
                "FALHA",
                "Módulo não encontrado.",
            )

    # pytest é necessário para desenvolvimento,
    # mas não para todas as operações do agente.

    if find_spec("pytest") is not None:
        registrar(
            "Python: pytest",
            "OK",
            "Ferramenta de testes disponível.",
        )
    else:
        registrar(
            "Python: pytest",
            "AVISO",
            "pytest não está instalado.",
        )

    # ------------------------------------------
    # 3. Arquivos essenciais
    # ------------------------------------------

    for caminho in ARQUIVOS_ESSENCIAIS:

        arquivo = raiz / caminho

        if arquivo.is_file():
            registrar(
                caminho,
                "OK",
                "Arquivo encontrado.",
            )
        else:
            registrar(
                caminho,
                "FALHA",
                "Arquivo essencial ausente.",
            )

    # ------------------------------------------
    # 4. Configuração de autorização
    # ------------------------------------------

    configuracao = (
        raiz
        / "config"
        / "authorized_repositories.json"
    )

    if not configuracao.is_file():

        registrar(
            "Configuração de permissões",
            "AVISO",
        (
            "Configuração local ainda não criada. "
            "Nenhum repositório deve estar autorizado "
            "até a configuração inicial."
        ),
    )

    else:

        try:
            dados = json.loads(
                configuracao.read_text(
                    encoding="utf-8-sig"
                )
            )

            if not isinstance(
                dados,
                (dict, list),
            ):
                raise ValueError(
                    "Estrutura JSON inesperada."
                )

        except (
            OSError,
            UnicodeError,
            ValueError,
        ) as erro:

            registrar(
                "Configuração de permissões",
                "FALHA",
                f"JSON inválido: {erro}",
            )

        else:

            registrar(
                "Configuração de permissões",
                "OK",
                "Arquivo JSON válido.",
            )

    # ------------------------------------------
    # 5. Pastas de trabalho
    # ------------------------------------------

    for nome in ("workspace", "tests"):

        pasta = raiz / nome

        if pasta.is_dir():
            registrar(
                f"Pasta: {nome}",
                "OK",
                "Diretório encontrado.",
            )
        else:
            registrar(
                f"Pasta: {nome}",
                "AVISO",
                "Diretório não encontrado.",
            )

    return resultados


def exibir_diagnostico():
    """
    Apresenta o resultado e devolve um código
    apropriado para automação futura.
    """
    resultados = verificar_prontidao()

    from app.operational_doctor import verificar_servicos

    resultados.extend(
    verificar_servicos()
)

    print("\n" + "=" * 60)
    print("GITHUB AI AGENT - DIAGNÓSTICO V1.0")
    print("=" * 60)

    for item in resultados:
        print(
            f"[{item.status}] "
            f"{item.nome}: {item.detalhe}"
        )

    falhas = sum(
        item.status == "FALHA"
        for item in resultados
    )

    avisos = sum(
        item.status == "AVISO"
        for item in resultados
    )

    print("\n" + "=" * 60)
    print(f"Falhas: {falhas}")
    print(f"Avisos: {avisos}")

    if falhas:
        print(
            "Diagnóstico: existem requisitos "
            "essenciais pendentes."
        )
        return 1

    print(
        "Diagnóstico básico: "
        "requisitos locais encontrados."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(exibir_diagnostico())
