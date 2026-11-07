# Histórico de alterações (Changelog)

Todas as mudanças relevantes do **GitHub AI Agent** serão documentadas neste arquivo.

O formato segue as convenções do [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/), e o projeto pretende utilizar [Versionamento Semântico](https://semver.org/lang/pt-BR/) a partir da primeira versão publicada.

## V1.0.0 - 06/11/2026

### Adicionado

- **Integração com GitHub:** consulta de repositórios, branches e arquivos por meio do GitHub CLI (`gh`).
- **Análise de projetos Java:** identificação de classes, métodos, estrutura de diretórios, tecnologias, build e oportunidades de testes.
- **Análise de portfólio:** pontuação, recomendações e relatórios sobre os repositórios examinados.
- **Inteligência artificial local:** integração com Ollama e geração de respostas estruturadas e validadas em Python.
- **Planejador de evolução:** geração de planos de melhoria a partir de critérios verificáveis, com seleção de ações pelo usuário.
- **Executores supervisionados:** melhoria de README, configuração de Maven, organização de arquivos Java e geração assistida de testes.
- **Gerenciamento de repositórios autorizados:** controle local de quais repositórios podem receber operações do agente.
- **Fluxo Git supervisionado:** revisão de alterações, seleção de arquivos, criação de commits locais e publicação mediante aprovação.
- **Diagnóstico do ambiente:** verificações de dependências, arquivos essenciais, configuração, autenticação do GitHub CLI e disponibilidade do Ollama.
- **Suíte automatizada de testes:** testes unitários, de segurança, de integração Git e de aceitação local com repositórios temporários.

### Alterado

- A organização de arquivos Java passou a realizar movimentações locais sem preparar automaticamente o staging.
- O fluxo de commit passou a tentar recuperar o staging quando uma operação é cancelada ou falha antes da confirmação do commit.
- O módulo de commit passou a comparar o diff aprovado e o estado do `HEAD` para reconhecer alterações inesperadas e situações de resultado incerto.
- As ações sugeridas pela IA passaram a ser verificadas por regras e executores explicitamente registrados em Python.

### Segurança

- Aprovação humana exigida nos fluxos de modificação e publicação implementados.
- Bloqueio de ações não autorizadas, como `force_push`, exclusão de repositórios e execução arbitrária de comandos pela IA.
- Restrições de caminhos de escrita, incluindo bloqueio de acesso à pasta `.git`, travessia de diretórios e sobrescritas não revisadas.
- Verificação de alterações ocorridas entre a revisão de um arquivo e sua gravação.
- Preservação das alterações locais quando o commit é cancelado ou quando a recuperação do staging é possível.
- Interrupção da recuperação automática quando houver mudança inesperada no histórico ou no staging, exigindo inspeção manual.

### Validação

- Execução da suíte automatizada com `pytest`.
- Testes de operações Git em repositórios locais temporários, sem publicação no GitHub real.
- Homologação supervisionada em repositório GitHub separado, incluindo configuração Maven, reorganização da estrutura Java, commit e push.

---

## Não lançado

- Expandir e reforçar as verificações de segurança do código gerado por IA.
- Ampliar os testes de integração dos executores reais.
- Melhorar a interpretação de projetos Java e Spring Boot.
- Adicionar relatórios exportáveis sobre a evolução dos repositórios.
- Refinar a experiência do menu e os diagnósticos de falha.


> **Estado da versão:** a versão **1.0.0** está em preparação. Quando o release for efetivamente publicado, o conteúdo acima será consolidado em `## [1.0.0] - AAAA-MM-DD`, com a data real da publicação, e uma nova seção `## [Não lançado]` será aberta para mudanças futuras.
