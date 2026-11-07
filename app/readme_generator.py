def gerar_readme_basico(
    nome_projeto,
    descricao,
    linguagens,
):
    """
    Gera uma primeira versão de README.

    Esta função apenas produz texto.
    Não altera arquivos.
    """

    descricao = (
        descricao
        or "Projeto desenvolvido para estudos."
    )

    if linguagens:
        texto_linguagens = ", ".join(linguagens)
    else:
        texto_linguagens = "Não identificadas"

    return f"""# {nome_projeto}

## Sobre o projeto

{descricao}

## Tecnologias

- {texto_linguagens}

## Objetivo

Este repositório reúne códigos e exercícios desenvolvidos durante os estudos.

## Estrutura

Os arquivos do projeto estão organizados conforme os conteúdos estudados.

## Autor

Projeto desenvolvido para fins de estudo e construção de portfólio.
"""