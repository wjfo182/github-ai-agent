from app.repository import (
    analisar_portfolio_repositorio,
)

from app.repository_selector import (
    selecionar_repositorio,
)

from app.local_actions import (
    criar_readme_local,
)

from app.commit_actions import (
    criar_commit_controlado,
)

from app.push_actions import (
    publicar_branch_atual,
)

from app.permission_actions import (
    listar_repositorios_autorizados,
    revogar_autorizacao_interativa,
)

from app.ai_agent import analisar_com_ia
from app.ai_actions import melhorar_readme_com_ia
from app.ai_dispatcher import executar_fluxo_ia

from app.plan_actions import (
    exibir_plano_portfolio,
    executar_etapa_plano,
)

from app.doctor import exibir_diagnostico

def exibir_relatorio(analise):
    """
    Exibe a análise completa de um repositório.
    """

    basica = analise["analise_basica"]
    branches = analise["analise_branches"]

    print("\n" + "=" * 60)
    print("RELATÓRIO DO REPOSITÓRIO")
    print("=" * 60)

    print(
        f"\nRepositório: "
        f"{analise['repositorio']}"
    )

    # -------------------------------------------------
    # Informações gerais
    # -------------------------------------------------

    print("\n--- Informações gerais ---")

    linguagem_github = basica.get(
        "linguagem"
    )

    if linguagem_github:
        print(
            f"Linguagem informada pelo GitHub: "
            f"{linguagem_github}"
        )
    else:
        print(
            "Linguagem informada pelo GitHub: "
            "não identificada"
        )

    print(
        f"Branch padrão: "
        f"{branches['branch_padrao']}"
    )

    # -------------------------------------------------
    # Pontos positivos
    # -------------------------------------------------

    print("\n--- Pontos positivos ---")

    if basica["pontos_positivos"]:
        for ponto in basica[
            "pontos_positivos"
        ]:
            print(
                f"[+] {ponto}"
            )
    else:
        print(
            "Nenhum ponto positivo identificado."
        )

    # -------------------------------------------------
    # Pontos de atenção
    # -------------------------------------------------

    print("\n--- Pontos de atenção ---")

    if basica["problemas"]:
        for problema in basica["problemas"]:
            print(
                f"[!] {problema}"
            )
    else:
        print(
            "Nenhum problema identificado."
        )

    # -------------------------------------------------
    # Branches
    # -------------------------------------------------

    print("\n--- Branches ---")

    for nome_branch, dados in branches[
        "branches"
    ].items():

        marcador = ""

        if nome_branch == branches[
            "branch_padrao"
        ]:
            marcador = " (PADRÃO)"

        print(
            f"\nBranch: "
            f"{nome_branch}{marcador}"
        )

        linguagens = dados[
            "linguagens"
        ]

        if linguagens:
            print(
                "  Linguagens: "
                + ", ".join(linguagens)
            )
        else:
            print(
                "  Linguagens: nenhuma"
            )

        print(
            "  README.md: "
            + (
                "encontrado"
                if dados["possui_readme"]
                else "não encontrado"
            )
        )

        print(
            f"  Arquivos: "
            f"{len(dados['arquivos'])}"
        )

    # -------------------------------------------------
    # Java Backend
    # -------------------------------------------------

    print(
        "\n--- Análise Java Backend ---"
    )

    java = analise.get(
        "java_backend",
        {},
    )

    print(
        f"Branch usada para análise: "
        f"{analise.get('branch_analise')}"
    )

    print(
        "[+] Código Java encontrado."
        if java.get("java")
        else "[!] Código Java não encontrado."
    )

    if java.get("build_tool"):
        print(
            f"[+] Build: "
            f"{java['build_tool']}"
        )
    else:
        print(
            "[!] Maven ou Gradle "
            "não identificado."
        )

    print(
        "[+] Estrutura src/main/java encontrada."
        if java.get("estrutura_java_padrao")
        else
        "[!] Estrutura src/main/java não encontrada."
    )

    print(
        "[+] Estrutura de testes encontrada."
        if java.get("testes")
        else
        "[!] Estrutura src/test/java não encontrada."
    )

    print(
        "[+] .gitignore encontrado."
        if java.get("gitignore")
        else
        "[!] .gitignore não encontrado."
    )

    print(
        "[+] Docker encontrado."
        if java.get("docker")
        else
        "[!] Docker não identificado."
    )

    # -------------------------------------------------
    # Stack
    # -------------------------------------------------

    print("\n--- Stack detectada ---")

    stack = analise.get(
        "stack_java",
        {},
    )

    if stack.get("build_tool"):
        print(
            f"[+] Build: "
            f"{stack['build_tool']}"
        )

        print(
            f"[+] Arquivo: "
            f"{stack['build_file']}"
        )
    else:
        print(
            "[!] Arquivo de build "
            "não identificado."
        )

    tecnologias = (
        stack.get("tecnologias")
        or {}
    )

    tecnologias_exibicao = [
        ("Spring Boot", "spring_boot"),
        ("Spring Web", "spring_web"),
        (
            "Spring Data JPA",
            "spring_data_jpa",
        ),
        (
            "Spring Security",
            "spring_security",
        ),
        ("Validation", "validation"),
        ("PostgreSQL", "postgresql"),
        ("MySQL", "mysql"),
        ("H2", "h2"),
        ("Lombok", "lombok"),
        (
            "Spring Tests",
            "testes_spring",
        ),
        (
            "Swagger / OpenAPI",
            "swagger_openapi",
        ),
        ("Flyway", "flyway"),
        ("Liquibase", "liquibase"),
    ]

    encontrou_tecnologia = False

    for nome, chave in tecnologias_exibicao:

        if tecnologias.get(chave):
            encontrou_tecnologia = True
            print(
                f"[+] {nome}"
            )

    if not encontrou_tecnologia:
        print(
            "Nenhuma tecnologia Backend "
            "adicional identificada."
        )

    # -------------------------------------------------
    # Testabilidade
    # -------------------------------------------------

    print(
        "\n--- Elegibilidade para testes automáticos ---"
    )

    testes = analise.get(
        "elegibilidade_testes",
        {},
    )

    if testes.get("elegivel"):
        print(
            "[+] Projeto elegível para geração "
            "assistida de testes."
        )
    else:
        print(
            "[!] Projeto ainda não é elegível "
            "para geração automática de testes."
        )

    print(
        f"Arquivos Java encontrados: "
        f"{testes.get('quantidade_arquivos_java', 0)}"
    )

    if testes.get("build_tool"):
        print(
            f"Build: {testes['build_tool']}"
        )

    if testes.get("framework_testes"):
        print(
            f"Framework de testes: "
            f"{testes['framework_testes']}"
        )

    motivos = testes.get(
        "motivos_bloqueio",
        [],
    )

    if motivos:
        print("\nImpedimentos:")

        for motivo in motivos:
            print(
                f"  [-] {motivo}"
            )

            
    # -------------------------------------------------
    # Pontuação
    # -------------------------------------------------

    print(
        "\n--- Prontidão para "
        "Portfólio Java Backend ---"
    )

    avaliacao = analise.get(
        "pontuacao",
        {},
    )

    print(
        f"Pontuação: "
        f"{avaliacao.get('pontuacao', 0)}/"
        f"{avaliacao.get('maximo', 100)}"
    )

    print(
        f"Classificação: "
        f"{avaliacao.get('nivel', 'Não avaliado')}"
    )

    print("\nCritérios:")

    for nome, pontos, atendido in avaliacao.get(
        "criterios",
        [],
    ):
        marcador = (
            "[+]"
            if atendido
            else "[-]"
        )

        print(
            f"{marcador} "
            f"{nome} "
            f"({pontos} pontos)"
        )

    # -------------------------------------------------
    # Recomendações
    # -------------------------------------------------

    print(
        "\n--- Melhorias recomendadas ---"
    )

    recomendacoes = analise.get(
        "recomendacoes",
        [],
    )

    if not recomendacoes:
        print(
            "Nenhuma recomendação "
            "prioritária encontrada."
        )

    else:
        for indice, recomendacao in enumerate(
            recomendacoes,
            start=1,
        ):
            print(
                f"\n{indice}. "
                f"[{recomendacao['prioridade']}] "
                f"{recomendacao['titulo']}"
            )

            print(
                f"   Motivo: "
                f"{recomendacao['motivo']}"
            )

            print(
                f"   Ação: "
                f"{recomendacao['acao']}"
            )

    # -------------------------------------------------
    # Alertas
    # -------------------------------------------------

    print("\n--- Alertas ---")

    if branches["alertas"]:
        for alerta in branches[
            "alertas"
        ]:
            print(
                f"[!] {alerta}"
            )
    else:
        print(
            "Nenhum alerta encontrado."
        )

    print("\n" + "=" * 60)

def analisar_repositorio_interativo():
    """
    Seleciona e analisa um repositório.
    """

    nome_completo = selecionar_repositorio()

    print(
        f"\nAnalisando "
        f"{nome_completo}..."
    )

    analise = analisar_portfolio_repositorio(
        nome_completo
    )

    exibir_relatorio(
        analise
    )

def exibir_menu():
    """
    Exibe o menu principal.
    """

    print("\n" + "=" * 60)
    print("JAVA PORTFOLIO AGENT")
    print("=" * 60)

    print(
        "\n1. Analisar repositório"
    )

    print(
        "2. Criar README local"
    )

    print(
        "3. Criar commit local"
    )

    print(
        "4. Publicar commits"
    )

    print(
        "5. Ver repositórios autorizados"
    )

    print(
        "6. Revogar autorização"
    )
    print(
        "7. Analisar com IA"
)
    print(
    "8. Executar ação proposta pela IA"
)
    print(
    "9. Gerar plano de evolução"
)
    print(
    "10. Executar etapa do plano"
    )
    print(
        "11. Exibir diagnóstico"
    )
    print(
        "0. Sair"
    )

    print()

def main():
    """
    Loop principal da aplicação.
    """

    while True:

        try:
            exibir_menu()

            opcao = input(
                "Escolha uma opção: "
            ).strip()

            if opcao == "1":
                analisar_repositorio_interativo()

            elif opcao == "2":
                criar_readme_local()

            elif opcao == "3":
                criar_commit_controlado()

            elif opcao == "4":
                publicar_branch_atual()

            elif opcao == "5":
                listar_repositorios_autorizados()

            elif opcao == "6":
                revogar_autorizacao_interativa()

            elif opcao == "7":
                analisar_com_ia()
    
            elif opcao == "8":
                executar_fluxo_ia()

            elif opcao == "9":
                exibir_plano_portfolio()

            elif opcao == "10":
                executar_etapa_plano()

            elif opcao == "11":
                exibir_diagnostico()

            elif opcao == "0":
                print(
                    "\nEncerrando "
                    "Java Portfolio Agent."
                )
                break

            else:
                print(
                    "\nOpção inválida."
                )

            input(
                "\nPressione ENTER "
                "para voltar ao menu..."
            )

        except KeyboardInterrupt:
            print(
                "\n\nOperação interrompida."
            )

        except (
            RuntimeError,
            ValueError,
        ) as erro:
            print(
                f"\nErro: {erro}"
            )

            input(
                "\nPressione ENTER "
                "para voltar ao menu..."
            )


if __name__ == "__main__":
    main()