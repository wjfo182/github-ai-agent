import difflib
import json
from pathlib import Path

from app.ai_agent import gerar_analise_ia

from app.ai_models import ReadmeGeradoIA

from app.ai_provider import (
    consultar_ia_estruturada,
)

from app.approvals import (
    solicitar_aprovacao,
)

from app.git_manager import (
    clonar_repositorio,
    repositorio_esta_limpo,
    atualizar_todas_referencias,
    selecionar_branch,
    atualizar_branch_local_ff,
    escrever_arquivo_local,
    obter_diff_git,
)

from app.repository_selector import (
    selecionar_repositorio,
)

from app.security import (
    validar_acao_executavel,
)


SYSTEM_PROMPT_README = """
Você é especialista em documentação de projetos
de software e portfólio Java Backend.

Sua tarefa é melhorar um README existente.

Regras obrigatórias:

- Use somente as informações fornecidas.
- Não invente tecnologias.
- Não invente funcionalidades.
- Não invente comandos que não estejam comprovados.
- Preserve informações corretas do README atual.
- Escreva em português do Brasil.
- Produza Markdown limpo.
- Não coloque o Markdown dentro de blocos ```markdown.
- Não afirme que realizou alterações.
"""


def gerar_diff_memoria(
    conteudo_atual,
    conteudo_novo,
    caminho,
):
    """
    Cria um diff sem modificar o arquivo.
    """

    linhas_atuais = conteudo_atual.splitlines(
        keepends=True
    )

    linhas_novas = conteudo_novo.splitlines(
        keepends=True
    )

    diff = difflib.unified_diff(
        linhas_atuais,
        linhas_novas,
        fromfile=f"a/{caminho}",
        tofile=f"b/{caminho}",
    )

    return "".join(diff)


def melhorar_readme_com_ia():
    """
    Melhora um README existente usando IA.

    A IA gera conteúdo.
    O Python controla a execução.
    """

    nome_completo = selecionar_repositorio()

    print(
        f"\nAnalisando {nome_completo}..."
    )

    analise, analise_ia = gerar_analise_ia(
        nome_completo
    )

    # Procurar especificamente a proposta
    # melhorar_readme.
    proposta = next(
        (
            acao
            for acao in analise_ia.acoes_propostas
            if acao.tipo == "melhorar_readme"
        ),
        None,
    )

    if proposta is None:
        print(
            "\nA IA não recomendou melhorar "
            "o README deste repositório."
        )

        print(
            "Nenhuma alteração foi proposta."
        )

        return

    validar_acao_executavel(
        proposta.tipo
    )

    branch = analise["branch_analise"]

    dados_branch = analise[
        "analise_branches"
    ]["branches"][branch]

    caminho_readme = next(
        (
            arquivo
            for arquivo in dados_branch["arquivos"]
            if arquivo.lower() == "readme.md"
        ),
        None,
    )

    if caminho_readme is None:
        print(
            "\nREADME.md não encontrado "
            "na branch analisada."
        )

        print(
            "Use a ação de criação de README "
            "em vez desta ação."
        )

        return

    print("\n" + "=" * 60)
    print("PROPOSTA DA IA")
    print("=" * 60)

    print(
        f"\nPrioridade: "
        f"{proposta.prioridade.upper()}"
    )

    print(
        f"Título: {proposta.titulo}"
    )

    print(
        f"Motivo: {proposta.motivo}"
    )

    aprovado_plano = solicitar_aprovacao(
        "Gerar nova versão do README",
        [
            f"Repositório: {nome_completo}",
            f"Branch: {branch}",
            f"Arquivo: {caminho_readme}",
            (
                "A IA apenas gerará uma proposta "
                "de conteúdo."
            ),
            (
                "Nenhum arquivo será alterado "
                "neste momento."
            ),
        ],
    )

    if not aprovado_plano:
        print("\nOperação cancelada.")
        return

    # Preparar repositório local.
    repo = clonar_repositorio(
        nome_completo
    )

    if not repositorio_esta_limpo(repo):
        print(
            "\nExistem alterações locais "
            "não commitadas."
        )

        print(
            "A operação foi bloqueada."
        )

        return

    atualizar_todas_referencias(
        repo
    )

    selecionar_branch(
        repo,
        branch,
    )

    atualizar_branch_local_ff(
        repo,
        branch,
    )

    caminho_local = (
        Path(repo) / caminho_readme
    ).resolve()

    raiz = Path(repo).resolve()

    try:
        caminho_local.relative_to(
            raiz
        )

    except ValueError as erro:
        raise RuntimeError(
            "README fora do repositório autorizado."
        ) from erro

    if not caminho_local.exists():
        raise RuntimeError(
            "README local não encontrado."
        )

    conteudo_atual = caminho_local.read_text(
        encoding="utf-8"
    )

    contexto = json.dumps(
        analise,
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
Melhore o README abaixo para apresentação
profissional do repositório.

DADOS CONFIRMADOS DO REPOSITÓRIO:

{contexto}

README ATUAL:

{conteudo_atual}

Regras:

- Preserve fatos corretos.
- Não invente tecnologias.
- Não invente instruções de execução.
- Não invente dependências.
- Mantenha o README apropriado ao nível real
  do projeto.
- Se for um repositório de estudos, deixe isso claro.
"""

    mensagens = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT_README,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    print(
        "\nGerando proposta de README..."
    )

    readme_gerado = consultar_ia_estruturada(
        mensagens,
        ReadmeGeradoIA,
    )

    diff = gerar_diff_memoria(
        conteudo_atual,
        readme_gerado.conteudo_markdown,
        caminho_readme,
    )

    print("\n" + "=" * 60)
    print("ALTERAÇÕES PROPOSTAS")
    print("=" * 60)

    for alteracao in (
        readme_gerado.alteracoes_principais
    ):
        print(
            f"[+] {alteracao}"
        )

    print("\nJustificativa:")
    print(
        readme_gerado.justificativa
    )

    print("\n" + "=" * 60)
    print("DIFF PROPOSTO")
    print("=" * 60)

    print(
        diff
        or "Nenhuma diferença encontrada."
    )

    if not diff:
        print(
            "\nA IA não produziu nenhuma "
            "alteração efetiva."
        )
        return

    aprovado_escrita = solicitar_aprovacao(
        "Aplicar novo README localmente",
        [
            f"Repositório: {nome_completo}",
            f"Branch: {branch}",
            f"Arquivo: {caminho_readme}",
            (
                "Aplicar exatamente o conteúdo "
                "mostrado no diff."
            ),
            "Não realizar commit.",
            "Não realizar push.",
        ],
    )

    if not aprovado_escrita:
        print(
            "\nAlteração não aplicada."
        )
        return

    escrever_arquivo_local(
        repo,
        caminho_readme,
        readme_gerado.conteudo_markdown,
        sobrescrever=True,
    )

    print("\n" + "=" * 60)
    print("ALTERAÇÃO LOCAL REALIZADA")
    print("=" * 60)

    diff_real = obter_diff_git(
        repo
    )

    print(
        diff_real
        or "Nenhuma diferença encontrada."
    )

    print(
        "\nNenhum commit foi realizado."
    )

    print(
        "Nenhum push foi realizado."
    )


def main():
    try:
        melhorar_readme_com_ia()

    except (
        RuntimeError,
        ValueError,
    ) as erro:
        print(
            f"\nNão foi possível executar "
            f"a ação da IA: {erro}"
        )

def executar_melhorar_readme(
    nome_completo,
    analise,
    proposta,
):
    """
    Executor seguro da ação melhorar_readme.

    Recebe uma ação previamente validada.
    A IA não chama esta função diretamente.
    """

    validar_acao_executavel(
        proposta.tipo
    )

    if proposta.tipo != "melhorar_readme":
        raise RuntimeError(
            "Executor recebeu um tipo de ação incompatível."
        )

    branch = analise["branch_analise"]

    dados_branch = analise[
        "analise_branches"
    ]["branches"][branch]

    caminho_readme = next(
        (
            arquivo
            for arquivo in dados_branch["arquivos"]
            if arquivo.lower() == "readme.md"
        ),
        None,
    )

    if caminho_readme is None:
        print(
            "\nREADME.md não encontrado "
            "na branch analisada."
        )
        return

    print("\n" + "=" * 60)
    print("AÇÃO PROPOSTA PELA IA")
    print("=" * 60)

    print(f"\nTipo: {proposta.tipo}")
    print(f"Prioridade: {proposta.prioridade.upper()}")
    print(f"Título: {proposta.titulo}")
    print(f"Motivo: {proposta.motivo}")

    aprovado_plano = solicitar_aprovacao(
        "Gerar uma nova versão do README",
        [
            f"Repositório: {nome_completo}",
            f"Branch: {branch}",
            f"Arquivo: {caminho_readme}",
            "A IA somente gerará uma proposta.",
            "Nenhum arquivo será alterado ainda.",
        ],
    )

    if not aprovado_plano:
        print("\nOperação cancelada.")
        return

    repo = clonar_repositorio(
        nome_completo
    )

    if not repositorio_esta_limpo(repo):
        print(
            "\nExistem alterações locais não commitadas."
        )
        print(
            "A operação foi bloqueada por segurança."
        )
        return

    atualizar_todas_referencias(
        repo
    )

    selecionar_branch(
        repo,
        branch,
    )

    atualizar_branch_local_ff(
        repo,
        branch,
    )

    raiz = Path(repo).resolve()

    caminho_local = (
        raiz / caminho_readme
    ).resolve()

    try:
        caminho_local.relative_to(raiz)

    except ValueError as erro:
        raise RuntimeError(
            "README fora do repositório autorizado."
        ) from erro

    if not caminho_local.exists():
        raise RuntimeError(
            "README local não encontrado."
        )

    conteudo_atual = caminho_local.read_text(
        encoding="utf-8"
    )

    contexto = json.dumps(
        analise,
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
Melhore o README abaixo para apresentação
profissional deste repositório.

DADOS CONFIRMADOS:

{contexto}

README ATUAL:

{conteudo_atual}

Regras:

- Não invente tecnologias.
- Não invente funcionalidades.
- Não invente comandos.
- Preserve informações verdadeiras.
- Respeite o nível real do projeto.
- Se for um repositório de estudos, deixe isso claro.
"""

    mensagens = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT_README,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    print("\nGerando proposta de README...")

    readme_gerado = consultar_ia_estruturada(
        mensagens,
        ReadmeGeradoIA,
    )

    diff = gerar_diff_memoria(
        conteudo_atual,
        readme_gerado.conteudo_markdown,
        caminho_readme,
    )

    if not diff:
        print(
            "\nA IA não produziu alterações efetivas."
        )
        return

    print("\n" + "=" * 60)
    print("DIFF PROPOSTO")
    print("=" * 60)

    print(diff)

    print("\nAlterações principais:")

    for alteracao in (
        readme_gerado.alteracoes_principais
    ):
        print(f"  [+] {alteracao}")

    print("\nJustificativa:")
    print(readme_gerado.justificativa)

    aprovado_escrita = solicitar_aprovacao(
        "Aplicar alteração local",
        [
            f"Arquivo: {caminho_readme}",
            "Aplicar exatamente o conteúdo revisado.",
            "Não realizar commit.",
            "Não realizar push.",
        ],
    )

    if not aprovado_escrita:
        print("\nAlteração não aplicada.")
        return

    escrever_arquivo_local(
        repo,
        caminho_readme,
        readme_gerado.conteudo_markdown,
        sobrescrever=True,
        conteudo_esperado=conteudo_atual,
)

    print("\n" + "=" * 60)
    print("ALTERAÇÃO LOCAL REALIZADA")
    print("=" * 60)

    print(
        obter_diff_git(repo)
        or "Nenhuma diferença encontrada."
    )

    print("\nNenhum commit foi realizado.")
    print("Nenhum push foi realizado.")

if __name__ == "__main__":
    main()