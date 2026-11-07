import json

from app.ai_provider import consultar_ia_estruturada
from app.ai_models import AnaliseIA
from app.security import validar_acoes

from app.repository import (
    analisar_portfolio_repositorio,
)

from app.repository_selector import (
    selecionar_repositorio,
)

CATALOGO_ACOES = """
CATÁLOGO OBRIGATÓRIO DE AÇÕES:

melhorar_readme
- Use somente para criar ou melhorar README.md.
- Não use para estrutura Java, build ou testes.

organizar_estrutura
- Use para organização de diretórios e arquivos.
- Exemplos:
  src/Main.java -> src/main/java/Main.java
  organização de packages
  estrutura padrão de projeto Java.
- Não use revisar_visibilidade para isso.

adicionar_testes
- Use somente quando a recomendação for criar
  ou melhorar testes automatizados.
- Não use para recomendar Maven ou Gradle.
- Não use para reorganizar código.

configurar_build
- Use quando a recomendação envolver:
  Maven
  Gradle
  pom.xml
  build.gradle
  dependências
  configuração de build.
- Se há Java mas nenhum build tool foi detectado,
  este é o tipo correto.

adicionar_documentacao
- Use para documentação adicional que não seja
  simplesmente melhorar o README.

revisar_visibilidade
- Use SOMENTE para tornar o repositório
  público/privado ou revisar sua visibilidade.
- Nunca use para estrutura de arquivos.

adicionar_topics
- Use SOMENTE para adicionar ou melhorar
  os topics do GitHub.

REGRAS:

- O campo tipo deve representar exatamente
  a ação descrita no título e no motivo.
- Não escolha um tipo apenas por ser parecido.
- Não invente novos tipos.
- Não use adicionar_testes para problemas de build.
- Não use revisar_visibilidade para problemas
  de estrutura.
- Não repita tipos desnecessariamente.
- É melhor retornar menos ações corretas do que
  cinco ações classificadas incorretamente.
"""

SYSTEM_PROMPT = """
Você é um assistente especializado em análise
de portfólio para desenvolvedores Java Backend.

Você receberá dados estruturados obtidos diretamente
de um repositório GitHub.

Regras obrigatórias:

1. Use somente os dados fornecidos.
2. Não invente arquivos, frameworks ou tecnologias.
3. Não afirme que realizou alterações.
4. Não execute comandos.
5. Não sugira force push.
6. Não sugira exclusões destrutivas sem necessidade.
7. Diferencie:
   - repositório de estudos;
   - projeto Java;
   - projeto Java Backend.
8. Priorize melhorias úteis para apresentação
   profissional do portfólio.
9. Responda em português do Brasil.
10. Seja objetivo e explique o motivo das recomendações.
"""

SYSTEM_PROMPT = (
    SYSTEM_PROMPT
    + "\n\n"
    + CATALOGO_ACOES
)


def montar_prompt(analise):
    """
    Converte a análise determinística do Python
    em contexto para a IA.
    """

    dados = json.dumps(
        analise,
        ensure_ascii=False,
        indent=2,
    )

    return f"""
Analise este repositório usando exclusivamente
os dados fornecidos.

DADOS DO REPOSITÓRIO:

{dados}

Regras adicionais:

- Proponha no máximo 5 ações.
- Use somente tipos permitidos pelo schema.
- Não invente arquivos.
- Não invente tecnologias.
- Não proponha comandos de terminal.
- Não proponha force push.
- Não proponha exclusão de repositório.
- Diferencie estudos de um projeto backend real.

REGRAS DE CLASSIFICAÇÃO DE AÇÃO:

- Ausência de Maven/Gradle:
  use configurar_build.

- Ausência de src/main/java ou estrutura inadequada:
  use organizar_estrutura.

- Ausência de testes:
  use adicionar_testes somente quando estiver
  falando realmente da criação de testes.

- Repositório privado:
  use revisar_visibilidade.

- Ausência de topics:
  use adicionar_topics.

- Problemas no README:
  use melhorar_readme.

Nunca use adicionar_testes como substituto
para configurar_build.

Nunca use revisar_visibilidade como substituto
para organizar_estrutura.

Retorne somente ações cujo tipo corresponda
ao título e ao motivo.
"""


def gerar_analise_ia(nome_completo):
    """
    Executa a análise estruturada da IA
    para um repositório já selecionado.

    Não realiza nenhuma alteração.
    """

    analise = analisar_portfolio_repositorio(
        nome_completo
    )

    prompt = montar_prompt(
        analise
    )

    mensagens = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    resultado = consultar_ia_estruturada(
        mensagens,
        AnaliseIA,
    )

    validar_acoes(
        resultado.acoes_propostas
    )

    return analise, resultado

def analisar_com_ia():
    """
    Analisa um repositório usando IA local,
    retornando apenas dados estruturados.

    Nenhuma ação é executada.
    """

    nome_completo = selecionar_repositorio()

    print(
        f"\nColetando dados de {nome_completo}..."
    )

    print("\nConsultando IA local...")

    analise, resultado = gerar_analise_ia(
        nome_completo
    )
    analise = analisar_portfolio_repositorio(
        nome_completo
    )

    # Segunda barreira:
    # mesmo depois da validação Pydantic,
    # o Python verifica a allowlist.
    validar_acoes(
        resultado.acoes_propostas
    )

    print("\n" + "=" * 60)
    print("ANÁLISE ESTRUTURADA DA IA")
    print("=" * 60)

    print(
        f"\nClassificação: "
        f"{resultado.classificacao}"
    )

    print("\nResumo:")
    print(resultado.resumo)

    print("\nPontos positivos:")

    for ponto in resultado.pontos_positivos:
        print(f"  [+] {ponto}")

    print("\nAções propostas:")

    if not resultado.acoes_propostas:
        print(
            "  Nenhuma ação proposta."
        )

    for indice, acao in enumerate(
        resultado.acoes_propostas,
        start=1,
    ):
        print(
            f"\n  {indice}. "
            f"[{acao.prioridade.upper()}] "
            f"{acao.titulo}"
        )

        print(
            f"     Tipo: {acao.tipo}"
        )

        print(
            f"     Motivo: {acao.motivo}"
        )

    print("\nPróximo passo:")
    print(resultado.proximo_passo)

    print("\n" + "=" * 60)

    print(
        "Nenhuma ação foi executada. "
        "As propostas passaram apenas "
        "pela validação de segurança."
    )

    return resultado

def main():
    try:
        analisar_com_ia()

    except (
        RuntimeError,
        ValueError,
    ) as erro:
        print(
            f"\nNão foi possível realizar "
            f"a análise com IA: {erro}"
        )


if __name__ == "__main__":
    main()