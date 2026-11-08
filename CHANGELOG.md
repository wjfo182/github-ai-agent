# Histórico de alterações (Changelog)

Todas as mudanças relevantes do **GitHub AI Agent** são documentadas neste arquivo.

O formato segue as convenções do [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/), e o projeto utiliza como referência o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

Nenhuma alteração registrada após a preparação da versão 1.0.0.

## [1.0.0] - 2026-11-08

### Adicionado

- **Integração com GitHub:** consulta de repositórios, branches e arquivos por meio do GitHub CLI (`gh`).
- **Análise de projetos Java:** identificação de classes, métodos, estrutura de diretórios, tecnologias, configuração de build e oportunidades de testes.
- **Análise de portfólio:** pontuação, recomendações e relatórios sobre os repositórios examinados.
- **Inteligência artificial local:** integração com Ollama e geração de respostas estruturadas e validadas em Python.
- **Planejador de evolução:** geração de planos de melhoria a partir de critérios verificáveis, com seleção de ações pelo usuário.
- **Executores supervisionados:** melhoria de README, configuração de Maven, organização de arquivos Java e geração assistida de testes.
- **Gerenciamento de repositórios autorizados:** controle local de quais repositórios podem receber operações do agente, por meio de `config/authorized_repositories.json`.
- **Fluxo Git supervisionado:** revisão de alterações, seleção de arquivos, criação de commits locais e publicação mediante aprovação humana.
- **Diagnóstico do ambiente:** verificações de dependências, arquivos essenciais, configuração local, autenticação do GitHub CLI e disponibilidade do Ollama.
- **Identificação de versão:** módulo `app/version.py` para consultar a versão do aplicativo.
- **Suíte automatizada de testes:** testes unitários, de segurança, de integração Git e de aceitação local com repositórios temporários.

### Alterado

- A organização de arquivos Java passou a realizar movimentações locais sem preparar automaticamente o *staging*.
- O fluxo de commit passou a tentar recuperar o *staging* quando uma operação é cancelada ou falha antes da confirmação do commit.
- O módulo de commit passou a comparar o *diff* aprovado e o estado do `HEAD` para reconhecer alterações inesperadas e situações de resultado incerto.
- As ações sugeridas pela IA passaram a ser verificadas por regras e executores explicitamente registrados em Python.
- O diagnóstico passou a tratar a ausência do arquivo local de autorizações em uma instalação nova como um aviso, sem conceder permissões automaticamente.
- O carregamento de autorizações passou a validar a estrutura do JSON e a lista de nomes de repositórios, bloqueando configurações inválidas.

### Segurança

- Aprovação humana exigida nos fluxos implementados de modificação e publicação.
- Bloqueio de ações não autorizadas, como `force_push`, exclusão de repositórios e execução arbitrária de comandos pela IA.
- Restrições de caminhos de escrita, incluindo bloqueio de acesso à pasta `.git`, travessia de diretórios e sobrescritas não revisadas.
- Verificação de alterações ocorridas entre a revisão de um arquivo e sua gravação.
- Preservação das alterações locais quando o commit é cancelado ou quando a recuperação do *staging* é possível.
- Interrupção da recuperação automática quando houver mudança inesperada no histórico ou no *staging*, exigindo inspeção manual.
- **Permissões explícitas:** operações de commit, execução de ações assistidas por IA e publicação verificam a autorização do repositório antes de prosseguir.
- **Instalação segura:** a ausência do arquivo de autorizações implica lista vazia; um arquivo inválido bloqueia a consulta ou a operação, em vez de liberar permissões.
- **Validação de destino remoto:** conferência do `origin` para comparar as URLs efetivas de consulta e de publicação com o repositório autorizado.
- **Proteção do push:** rejeição de destinos divergentes, hosts inesperados e configurações ambíguas com múltiplas URLs de publicação, aceitando formatos HTTPS e SSH previstos para `github.com`.
- **Revalidação antes da publicação:** nova conferência do destino remoto imediatamente antes das rotinas de push implementadas.
- **Configuração privada:** exclusão do arquivo local de autorizações e de outros arquivos sensíveis do controle de versão por meio de regras de `.gitignore`.

### Validação

- Execução da suíte automatizada com `pytest`, incluindo testes de regressão.
- Testes de operações Git em repositórios locais temporários, sem publicação no GitHub real durante esses testes.
- Testes de permissões para instalação nova, autorização explícita, revogação, configuração inválida e isolamento por repositório.
- Testes de bloqueio da criação de commits e de ações do dispatcher antes de acessar um repositório não autorizado.
- Testes de publicação simulada para autorização, recusa e aprovação de push em branch existente ou nova branch.
- Testes de validação de destino remoto com URLs HTTPS e SSH, `pushurl` divergente, múltiplos destinos e ausência de `origin`.
- Testes do formato e da identificação da versão `1.0.0`.
- Homologação supervisionada em repositório GitHub separado, incluindo configuração Maven, reorganização da estrutura Java, commit e push.
- Verificação de instalação limpa a partir de clone separado, sem herdar as autorizações locais do desenvolvedor.

### Limitações conhecidas

- O agente é supervisionado: operações de escrita e publicação exigem revisão e aprovação humana nos fluxos implementados.
- A análise de código Java e a geração assistida de testes não substituem revisão de segurança ou auditoria especializada; revise o código gerado antes de executá-lo.
- As verificações locais de segurança não oferecem isolamento completo contra processos maliciosos ou modificações concorrentes no ambiente.
- A disponibilidade dos recursos depende das ferramentas externas configuradas, incluindo Git, GitHub CLI e, para IA local, Ollama.

---

> **Nota de lançamento:** esta seção documenta o conteúdo planejado para `v1.0.0`. Confirme a data e publique a tag e o GitHub Release somente após a validação final do commit e da instalação limpa.
