from typing import Literal

from pydantic import BaseModel, Field


TipoAcao = Literal[
    "melhorar_readme",
    "organizar_estrutura",
    "adicionar_testes",
    "configurar_build",
    "adicionar_documentacao",
    "revisar_visibilidade",
    "adicionar_topics",
]

Prioridade = Literal[
    "alta",
    "media",
    "baixa",
]

Classificacao = Literal[
    "repositorio_estudos",
    "projeto_java",
    "projeto_java_backend",
]


class AcaoProposta(BaseModel):
    tipo: TipoAcao = Field(
        description=(
            "Tipo exato da ação. "
            "Use configurar_build para Maven/Gradle; "
            "organizar_estrutura para diretórios e "
            "estrutura Java; adicionar_testes somente "
            "para criação de testes; "
            "revisar_visibilidade somente para "
            "visibilidade pública/privada; "
            "adicionar_topics somente para topics; "
            "melhorar_readme somente para README."
        )
    )

    prioridade: Prioridade

    titulo: str = Field(
        min_length=3,
        max_length=100,
    )

    motivo: str = Field(
        min_length=5,
        max_length=500,
    )

class AnaliseIA(BaseModel):
    classificacao: Classificacao

    resumo: str = Field(
        min_length=10,
        max_length=1000,
    )

    pontos_positivos: list[str] = Field(
        max_length=3,
    )

    acoes_propostas: list[AcaoProposta] = Field(
        max_length=5,
    )

    proximo_passo: str = Field(
        min_length=5,
        max_length=500,
    )

class ReadmeGeradoIA(BaseModel):
    conteudo_markdown: str = Field(
        min_length=20,
    )

    alteracoes_principais: list[str] = Field(
        max_length=6,
    )

    justificativa: str = Field(
        min_length=10,
        max_length=800,
    )

class TesteJavaGeradoIA(BaseModel):
    conteudo_java: str = Field(
        min_length=30,
    )

    metodos_testados: list[str] = Field(
        max_length=10,
    )

    justificativa: str = Field(
        min_length=10,
        max_length=800,
    )