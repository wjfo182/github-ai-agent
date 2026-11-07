import difflib
from pathlib import Path

from app.ai_models import (
    TesteJavaGeradoIA,
)

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
    obter_revisao_local,
)

from app.java_analyzer import (
    calcular_caminho_teste,
)

from app.security import (
    validar_geracao_testes,
    validar_conteudo_teste_java,
)


SYSTEM_PROMPT_TESTES = """
Você gera exclusivamente testes unitários Java.

Regras obrigatórias:

- Use somente o código-fonte fornecido.
- Não invente métodos.
- Não invente construtores.
- Não invente dependências.
- Não acesse rede.
- Não execute processos.
- Não manipule arquivos.
- Não use System.exit.
- Não crie método main.
- Use somente bibliotecas de teste informadas.
- O código deve compilar dentro do projeto fornecido.
- Produza apenas um teste compatível com a classe alvo.
"""


def gerar_diff_novo_arquivo(
    caminho,
    conteudo,
):
    """
    Gera um diff para um arquivo que
    ainda não existe.
    """

    linhas = conteudo.splitlines(
        keepends=True
    )

    diff = difflib.unified_diff(
        [],
        linhas,
        fromfile="/dev/null",
        tofile=f"b/{caminho}",
    )

    return "".join(diff)

def executar_adicionar_testes(
    nome_completo,
    analise,
    proposta,
):
    """
    Executor seguro da ação adicionar_testes.
    """

    if proposta.tipo != "adicionar_testes":
        raise RuntimeError(
            "Executor recebeu uma ação incompatível."
        )

    candidatos = validar_geracao_testes(
        analise
    )

    if not isinstance(candidatos, list):
        raise RuntimeError(
        "A validação de testes retornou "
        "um formato inesperado."
    )

    framework = analise[
        "elegibilidade_testes"
    ]["framework_testes"]

    # Nesta primeira versão:
    # teste de Service só será gerado quando
    # Spring Boot Test estiver disponível.
    candidatos_filtrados = []

    for candidato in candidatos:

        tipo = candidato.get(
            "tipo_teste"
        )

        if tipo == "unitario":
            candidatos_filtrados.append(
                candidato
            )

        elif (
            tipo == "unitario_service"
            and framework == "Spring Boot Test"
        ):
            candidatos_filtrados.append(
                candidato
            )

    if not candidatos_filtrados:
        raise RuntimeError(
            "Nenhum candidato possui uma combinação "
            "de classe e framework suportada."
        )

    print("\n" + "=" * 60)
    print("CLASSES CANDIDATAS A TESTE")
    print("=" * 60)

    for indice, candidato in enumerate(
        candidatos_filtrados,
        start=1,
    ):
        print(
            f"\n{indice}. "
            f"{candidato['classe']}"
        )

        print(
            f"   Arquivo: "
            f"{candidato['arquivo']}"
        )

        print(
            f"   Tipo: "
            f"{candidato['tipo_teste']}"
        )

        print(
            f"   Motivo: "
            f"{candidato['motivo']}"
        )

    escolha = input(
        "\nEscolha a classe para gerar o teste: "
    ).strip()

    if not escolha.isdigit():
        raise RuntimeError(
            "Seleção inválida."
        )

    indice = int(escolha)

    if not 1 <= indice <= len(
        candidatos_filtrados
    ):
        raise RuntimeError(
            "Seleção fora do intervalo."
        )

    candidato = candidatos_filtrados[
        indice - 1
    ]

    arquivo_origem = candidato[
        "arquivo"
    ]

    classe_origem = candidato[
        "classe"
    ]

    # Localiza os dados estruturais da classe.
    estrutura = next(
        (
            item
            for item in analise[
                "estrutura_codigo_java"
            ]
            if item.get("arquivo")
            == arquivo_origem
        ),
        None,
    )

    if estrutura is None:
        raise RuntimeError(
            "Estrutura da classe selecionada "
            "não foi encontrada."
        )

    package = estrutura.get(
        "package"
    )

    classe_teste = (
        f"{classe_origem}Test"
    )

    caminho_teste = calcular_caminho_teste(
        arquivo_origem,
        classe_origem,
    )

    print("\nTeste planejado:")

    print(
        f"Classe original: {classe_origem}"
    )

    print(
        f"Arquivo original: {arquivo_origem}"
    )

    print(
        f"Framework: {framework}"
    )

    print(
        f"Classe de teste: {classe_teste}"
    )

    print(
        f"Destino: {caminho_teste}"
    )

    aprovado = solicitar_aprovacao(
        "Gerar proposta de teste",
        [
            f"Repositório: {nome_completo}",
            f"Classe: {classe_origem}",
            f"Destino: {caminho_teste}",
            (
                "Nenhum arquivo será criado "
                "nesta etapa."
            ),
        ],
    )

    if not aprovado:
        print(
            "\nGeração cancelada."
        )
        return

    # -----------------------------------------
    # Preparar repositório local
    # -----------------------------------------

    repo = clonar_repositorio(
        nome_completo
    )

    if not repositorio_esta_limpo(
        repo
    ):
        raise RuntimeError(
            "Existem alterações locais. "
            "Geração de teste bloqueada."
        )

    atualizar_todas_referencias(
        repo
    )

    branch = analise[
        "branch_analise"
    ]

    selecionar_branch(
        repo,
        branch,
    )

    atualizar_branch_local_ff(
        repo,
        branch,
    )

    raiz = Path(repo).resolve()

    origem_local = (
        raiz / arquivo_origem
    ).resolve()

    destino_local = (
        raiz / caminho_teste
    ).resolve()

    # -----------------------------------------
    # Proteção contra path traversal
    # -----------------------------------------

    try:
        origem_local.relative_to(
            raiz
        )

        destino_local.relative_to(
            raiz
        )

    except ValueError as erro:
        raise RuntimeError(
            "Caminho fora do repositório."
        ) from erro

    if not origem_local.is_file():
        raise RuntimeError(
            "Arquivo Java original "
            "não foi encontrado localmente."
        )

    if destino_local.exists():
        raise RuntimeError(
            "O arquivo de teste já existe. "
            "Nenhum arquivo será sobrescrito."
        )

    codigo_origem = origem_local.read_text(
        encoding="utf-8"
    )

    # -----------------------------------------
    # Bibliotecas permitidas
    # -----------------------------------------

    if framework == "Spring Boot Test":
        bibliotecas = (
            "JUnit Jupiter e Mockito, "
            "quando necessário"
        )

    else:
        bibliotecas = (
            "somente JUnit Jupiter"
        )

    prompt = f"""
Gere um teste unitário para a classe Java abaixo.

CLASSE ORIGINAL:
{classe_origem}

CLASSE DE TESTE OBRIGATÓRIA:
{classe_teste}

PACKAGE:
{package or "sem package"}

TIPO DE TESTE:
{candidato["tipo_teste"]}

FRAMEWORK DETECTADO:
{framework}

BIBLIOTECAS PERMITIDAS:
{bibliotecas}

CÓDIGO-FONTE REAL:

{codigo_origem}

Regras adicionais:

- A classe de teste deve se chamar exatamente
  {classe_teste}.
- Preserve o mesmo package da classe original.
- Não crie package se a classe original não tiver.
- Não invente métodos da classe original.
- Não teste métodos que não existem.
- Não acesse arquivos, rede ou processos.
- Não crie método main.
"""

    mensagens = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT_TESTES,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    print(
        "\nGerando proposta de teste..."
    )

    teste = consultar_ia_estruturada(
        mensagens,
        TesteJavaGeradoIA,
    )

    # -----------------------------------------
    # Validação depois da IA
    # -----------------------------------------

    validar_conteudo_teste_java(
        teste.conteudo_java,
        classe_teste,
        package,
    )

    diff = gerar_diff_novo_arquivo(
        caminho_teste,
        teste.conteudo_java,
    )

    print("\n" + "=" * 60)
    print("TESTE PROPOSTO")
    print("=" * 60)

    print("\nMétodos que a IA pretende testar:")

    for metodo in teste.metodos_testados:
        print(
            f"  [+] {metodo}"
        )

    print("\nJustificativa:")

    print(
        teste.justificativa
    )

    print("\n" + "=" * 60)
    print("DIFF")
    print("=" * 60)

    print(diff)

    aprovado_escrita = solicitar_aprovacao(
        "Criar arquivo de teste localmente",
        [
            f"Arquivo: {caminho_teste}",
            "Criar exatamente o conteúdo mostrado.",
            "Não realizar commit.",
            "Não realizar push.",
        ],
    )

    if not aprovado_escrita:
        print(
            "\nArquivo não criado."
        )
        return

    escrever_arquivo_local(
        repo,
        caminho_teste,
        teste.conteudo_java,
        sobrescrever=False,
    )

    print("\n" + "=" * 60)
    print("TESTE CRIADO LOCALMENTE")
    print("=" * 60)

    print(
        obter_revisao_local(repo)
    )

    print(
        "\nNenhum commit foi realizado."
    )

    print(
        "Nenhum push foi realizado."
    )