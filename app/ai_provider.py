from ollama import chat


MODELO_PADRAO = "qwen3:4b-instruct"


def consultar_ia(
    mensagens,
    modelo=MODELO_PADRAO,
):
    """
    Consulta o modelo local do Ollama.

    Esta função apenas envia texto ao modelo
    e recebe texto de volta.

    Não executa Git.
    Não executa comandos.
    Não modifica arquivos.
    """

    if not mensagens:
        raise ValueError(
            "A lista de mensagens não pode estar vazia."
        )

    try:
        resposta = chat(
            model=modelo,
            messages=mensagens,
            options={
                "temperature": 0.2,
            },
        )

    except Exception as erro:
        raise RuntimeError(
            f"Falha ao consultar a IA local: {erro}"
        ) from erro

    conteudo = resposta.message.content

    if not conteudo:
        raise RuntimeError(
            "A IA retornou uma resposta vazia."
        )

    return conteudo.strip()

def consultar_ia_estruturada(
    mensagens,
    modelo_resposta,
    modelo=MODELO_PADRAO,
):
    """
    Consulta o Ollama exigindo uma resposta
    compatível com um modelo Pydantic.
    """

    if not mensagens:
        raise ValueError(
            "A lista de mensagens não pode estar vazia."
        )

    try:
        resposta = chat(
            model=modelo,
            messages=mensagens,
            format=modelo_resposta.model_json_schema(),
            options={
                "temperature": 0,
            },
        )

    except Exception as erro:
        raise RuntimeError(
            f"Falha ao consultar a IA local: {erro}"
        ) from erro

    try:
        return modelo_resposta.model_validate_json(
            resposta.message.content
        )

    except Exception as erro:
        raise RuntimeError(
            "A resposta da IA não corresponde "
            "ao formato esperado."
        ) from erro