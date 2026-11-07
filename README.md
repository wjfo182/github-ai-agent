# GitHub AI Agent

**Agente local em Python para analisar, organizar e evoluir repositórios GitHub com apoio de IA e aprovação humana.**

O GitHub AI Agent foi desenvolvido para apoiar a manutenção de repositórios e a construção de portfólios de programação, com atenção especial a projetos **Java**. Ele combina análise determinística em Python, integração com o GitHub CLI (`gh`) e assistência de um modelo local executado pelo **Ollama**.

> **Status:** preparação da versão 1.0. O projeto já possui fluxos funcionais e testes automatizados, mas ainda está em fase de consolidação. As ações que modificam arquivos e as publicações exigem revisão e aprovação do usuário.

## Funcionalidades

- **Análise de repositórios:** consulta metadados, branches, arquivos, README e indicadores úteis para portfólio.
- **Análise Java:** identifica arquivos Java, classes, métodos, organização do código, ferramentas de build e oportunidades de testes.
- **Planejamento determinístico:** propõe uma sequência de melhorias a partir das condições detectadas, sem delegar à IA a escolha dos executores.
- **IA local:** utiliza Ollama para gerar análises estruturadas e auxiliar na elaboração de README e testes Java.
- **Ações supervisionadas:** permite melhorar README, configurar Maven, organizar diretórios Java e gerar testes em cenários suportados.
- **Git controlado:** prepara arquivos, apresenta diferenças, cria commits locais e publica alterações somente mediante aprovação.
- **Diagnóstico do ambiente:** verifica dependências, arquivos essenciais, configuração local, autenticação do GitHub CLI e disponibilidade do Ollama.
- **Testes automatizados:** cobre planejamento, regras de segurança, dispatcher, aprovações, manipulação de arquivos, operações Git e cenários de aceitação local.

## Como funciona

```text
GitHub / repositório local
           |
           v
   Análise em Python
           |
           v
 Planejamento de ações
           |
           v
  Seleção pelo usuário
           |
           v
 Verificação de permissões
           |
           v
 Executor especializado
           |
           v
 Revisão e aprovação
           |
           v
 Alteração local -> commit -> push
                  (cada etapa controlada)
```

A **IA recomenda ou gera conteúdo**, mas **não recebe permissão irrestrita para executar comandos**. As operações disponíveis são definidas no código Python e verificadas pelo dispatcher e pelas regras de segurança.

## Requisitos

| Componente | Finalidade |
| --- | --- |
| Windows com PowerShell | Ambiente utilizado no desenvolvimento e na homologação manual |
| Python | Executar o agente; ambiente de desenvolvimento utilizado: Python 3.15 |
| Git | Versionamento e operações locais |
| [GitHub CLI](https://cli.github.com/) (`gh`) | Consulta e autenticação no GitHub |
| [Ollama](https://ollama.com/) | Executar o modelo de IA local |
| Java JDK e Maven/Maven Wrapper | Opcionais para compilar e testar projetos Java analisados |

O agente usa bibliotecas Python como `pydantic` e `ollama`. O `pytest` é necessário para executar a suíte de testes, mas não para o uso cotidiano do menu.

## Instalação no Windows

No PowerShell, abra a pasta onde deseja trabalhar e obtenha uma cópia do projeto. **Substitua o endereço abaixo pela URL do repositório em que este agente será publicado:**

```powershell
git clone <URL_DO_REPOSITORIO_DO_AGENTE>
cd github-ai-agent
```

Crie e ative o ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências do aplicativo:

```powershell
python -m pip install -r requirements.txt
```

Para desenvolver e executar testes, use também:

```powershell
python -m pip install -r requirements-dev.txt
```

Autentique o GitHub CLI:

```powershell
gh auth login
gh auth status
```

Prepare o Ollama e um modelo compatível com a configuração do agente:

```powershell
ollama --version
ollama pull qwen3:4b-instruct
ollama list
```

O identificador do modelo deve corresponder ao configurado em `app/ai_provider.py`. O nome acima reflete o modelo utilizado durante o desenvolvimento; ajuste se sua instalação usar outro modelo.

> **Observação:** o projeto utiliza um arquivo local de autorizações em `config/authorized_repositories.json`. Ele não deve ser publicado com dados privados. Utilize o fluxo de autorização do menu para conceder acesso aos repositórios desejados.

## Execução

Execute o diagnóstico:

```powershell
python -m app.doctor
```

Inicie o menu:

```powershell
python -m app.main
```

### Menu principal

| Opção | Função |
| --- | --- |
| `1` | Analisar repositório |
| `2` | Criar README local |
| `3` | Criar commit local |
| `4` | Publicar commits |
| `5` | Ver repositórios autorizados |
| `6` | Revogar autorização |
| `7` | Analisar com IA |
| `8` | Executar ação proposta pela IA |
| `9` | Gerar plano de evolução |
| `10` | Executar etapa do plano |
| `11` | Verificar prontidão do agente |
| `0` | Sair |

O fluxo de **planejamento assistido** apresenta ações executáveis e recomendações sem executor. O agente não transforma automaticamente toda recomendação em uma operação.

### Exemplo: evoluir um projeto Java

1. Selecione um repositório e conceda autorização quando solicitado.
2. Use a opção `1` para analisar o projeto.
3. Use a opção `9` para identificar melhorias necessárias.
4. Se houver uma etapa executável, use a opção `10` e revise a proposta.
5. Aprove a modificação local apenas se o conteúdo e os caminhos estiverem corretos.
6. Use a opção `3` para revisar o staging e autorizar o commit.
7. Use a opção `4` para conferir a branch e autorizar o push.
8. Reanalise o repositório para verificar se a melhoria foi reconhecida.

A configuração de Maven e a movimentação de `src/Main.java` para `src/main/java/Main.java` foram exercitadas em um repositório separado de homologação.

## Estrutura do projeto

```text
github-ai-agent/
├── app/
│   ├── main.py                # Menu principal
│   ├── github_client.py       # Consultas ao GitHub
│   ├── repository.py          # Análise do repositório
│   ├── java_analyzer.py       # Inspeção de código Java
│   ├── planner.py             # Plano determinístico
│   ├── ai_provider.py         # Comunicação com Ollama
│   ├── ai_agent.py            # Análise assistida por IA
│   ├── ai_models.py           # Modelos de dados estruturados
│   ├── security.py            # Políticas de segurança
│   ├── ai_dispatcher.py       # Roteamento para executores
│   ├── ai_actions.py          # Melhorias de README
│   ├── test_actions.py        # Geração de testes Java
│   ├── build_actions.py       # Configuração de build
│   ├── structure_actions.py   # Organização de estrutura
│   ├── git_manager.py         # Operações Git locais
│   ├── commit_actions.py      # Commits supervisionados
│   ├── push_actions.py        # Publicação supervisionada
│   ├── approvals.py           # Aprovação humana
│   ├── doctor.py              # Diagnóstico estático
│   └── operational_doctor.py  # Diagnóstico operacional
├── config/                    # Configurações locais
├── tests/                     # Testes automatizados
├── workspace/                 # Cópias locais de repositórios
├── requirements.txt
└── requirements-dev.txt
```

A árvore apresenta os componentes centrais, não necessariamente todos os arquivos auxiliares.

## Segurança e limites

O projeto adota controles de defesa em camadas:

- **Repositórios autorizados:** ações locais são destinadas aos repositórios aprovados pelo usuário.
- **Executores explícitos:** somente tipos registrados e permitidos podem ser encaminhados para execução.
- **Aprovação antes de alterar ou publicar:** criação de arquivos, staging, commit e push são etapas supervisionadas.
- **Separação de responsabilidades:** gerar ou mover um arquivo não equivale a criar um commit, e criar um commit não equivale a publicar.
- **Proteção de caminhos:** a escrita centralizada restringe caminhos, impede modificações diretas em `.git/` e bloqueia sobrescritas não revisadas.
- **Recuperação de falhas:** o fluxo de commit tenta limpar o staging de sua operação quando falha antes de concluir; resultados incertos exigem inspeção manual.
- **Operações perigosas bloqueadas:** operações como `force_push`, exclusão de repositórios e execução arbitrária de shell não pertencem ao conjunto de ações executáveis.

**Limitações:** as verificações de conteúdo Java por padrões de texto não substituem uma análise de segurança do código. Testes gerados por IA podem conter instruções indesejadas e devem ser revisados antes de sua compilação ou execução. O projeto também não oferece isolamento completo contra processos locais maliciosos ou alterações concorrentes no repositório. Não utilize o agente como executor autônomo e irrestrito em repositórios sensíveis.

## Testes

Instale as dependências de desenvolvimento e execute:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

Para uma execução resumida:

```powershell
python -m pytest tests/ -q
```

A suíte inclui testes unitários, simulações com `monkeypatch`, cenários de Git real em diretórios temporários e testes de aceitação local. O total de testes pode mudar conforme o projeto evolui; utilize o resultado do comando para consultar a contagem atual.

## Homologação e estado da versão

Os fluxos de **configuração Maven**, **organização de diretórios Java**, **commit supervisionado** e **publicação no GitHub** foram experimentados em um repositório isolado de homologação, preservando os projetos de portfólio.

A versão 1.0 ainda requer revisão final de documentação, inventário de dependências, validação das permissões e verificação dos arquivos que serão incluídos no repositório público.

## Próximas melhorias

- Expandir e reforçar as verificações de segurança do código gerado por IA.
- Ampliar os testes de integração dos executores reais.
- Melhorar a interpretação de projetos Java e Spring Boot.
- Adicionar relatórios exportáveis sobre a evolução dos repositórios.
- Refinar a experiência do menu e os diagnósticos de falha.


## Licença

Este projeto é disponibilizado sob a Licença MIT.

Você pode utilizar, modificar e distribuir o código,
inclusive comercialmente, respeitando as condições da licença.

Consulte o arquivo [LICENSE](LICENSE) para mais informações.

---

*Projeto desenvolvido para estudo de Python, automação, integração com GitHub, análise de código Java e uso supervisionado de IA local.*
