import os
import tempfile
from pathlib import Path, PurePosixPath
import subprocess


BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BASE_DIR / "workspace"


def executar_comando(
    comando,
    diretorio=None,
    timeout=60,
):
    """
    Executa um comando controlado.

    Não utiliza shell=True.
    """

    try:
        resultado = subprocess.run(
            comando,
            cwd=diretorio,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )

        return resultado.stdout.strip()

    except FileNotFoundError as erro:
        raise RuntimeError(
            f"Comando não encontrado: {comando[0]}"
        ) from erro

    except subprocess.CalledProcessError as erro:
        mensagem = (
            erro.stderr.strip()
            or erro.stdout.strip()
        )

        raise RuntimeError(
            f"Falha ao executar comando: {mensagem}"
        ) from erro

    except subprocess.TimeoutExpired as erro:
        raise RuntimeError(
            "O comando excedeu o tempo limite."
        ) from erro

def clonar_repositorio(nome_completo):
    """
    Clona um repositório autorizado para a pasta workspace.

    Não altera o repositório remoto.
    """

    if not nome_completo or "/" not in nome_completo:
        raise ValueError(
            "Informe o repositório no formato usuario/repositorio."
        )

    nome_repositorio = nome_completo.split("/")[-1]

    WORKSPACE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    destino = WORKSPACE_DIR / nome_repositorio

    if destino.exists():
        if (destino / ".git").exists():
            return destino

        raise RuntimeError(
            f"O diretório '{destino}' já existe, "
            "mas não é um repositório Git."
        )

    comando = [
        "gh",
        "repo",
        "clone",
        nome_completo,
        str(destino),
    ]

    executar_comando(
        comando,
        diretorio=WORKSPACE_DIR,
        timeout=120,
    )

    return destino

def selecionar_branch(
    diretorio_repositorio,
    branch,
):
    """
    Seleciona uma branch na cópia local.
    """

    if not branch:
        raise ValueError(
            "Informe a branch."
        )

    executar_comando(
        [
            "git",
            "checkout",
            branch,
        ],
        diretorio=diretorio_repositorio,
    )

def obter_status_git(diretorio_repositorio):
    """
    Retorna o status atual do repositório local.
    """

    return executar_comando(
        [
            "git",
            "status",
            "--short",
            "--branch",
        ],
        diretorio=diretorio_repositorio,
    )

def repositorio_esta_limpo(diretorio_repositorio):
    """
    Verifica se existem alterações locais não commitadas.
    """

    resultado = executar_comando(
        [
            "git",
            "status",
            "--porcelain",
        ],
        diretorio=diretorio_repositorio,
    )

    return resultado == ""

def _destino_seguro(
    diretorio_repositorio,
    caminho_relativo,
):
    """
    Valida um destino de escrita dentro
    de um repositório local.

    Bloqueia:
    - caminhos absolutos;
    - saída do repositório;
    - acesso à pasta .git;
    - links simbólicos e junctions;
    - caminhos Windows inesperados.
    """

    if (
        not isinstance(caminho_relativo, str)
        or not caminho_relativo.strip()
    ):
        raise RuntimeError(
            "Caminho de arquivo inválido."
        )

    if (
        "\\" in caminho_relativo
        or ":" in caminho_relativo
    ):
        raise RuntimeError(
            "Caminho de arquivo inválido."
        )

    caminho = PurePosixPath(
        caminho_relativo
    )

    if (
        caminho.is_absolute()
        or ".." in caminho.parts
        or not caminho.parts
    ):
        raise RuntimeError(
            "Caminho fora do repositório."
        )

    if any(
        parte.lower() == ".git"
        for parte in caminho.parts
    ):
        raise RuntimeError(
            "A pasta .git é protegida."
        )

    raiz = Path(
        diretorio_repositorio
    ).resolve()

    if not raiz.is_dir():
        raise RuntimeError(
            "Repositório local não encontrado."
        )

    destino = raiz.joinpath(
        *caminho.parts
    )

    atual = raiz

    for parte in caminho.parts:
        atual = atual / parte

        if (
            atual.is_symlink()
            or (
                hasattr(atual, "is_junction")
                and atual.is_junction()
            )
        ):
            raise RuntimeError(
                "Links e junctions não são "
                "permitidos no destino."
            )

    try:
        destino.resolve().relative_to(
            raiz
        )

    except ValueError as erro:
        raise RuntimeError(
            "Caminho fora do repositório."
        ) from erro

    return destino

def escrever_arquivo_local(
    diretorio_repositorio,
    caminho_relativo,
    conteudo,
    sobrescrever=False,
    *,
    conteudo_esperado=None,
):
    """
    Grava arquivos dentro do repositório.

    Regras:
    - Não permite sair do repositório.
    - Não permite modificar .git.
    - Não segue links no caminho de destino.
    - Não sobrescreve sem revisão anterior.
    - Não faz commit ou push.
    """

    if not isinstance(conteudo, str):
        raise TypeError(
            "O conteúdo precisa ser texto."
        )

    destino = _destino_seguro(
        diretorio_repositorio,
        caminho_relativo,
    )

    if sobrescrever and conteudo_esperado is None:
        raise RuntimeError(
            "Sobrescrita exige o conteúdo "
            "previamente revisado."
        )

    destino.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Validar novamente após criar diretórios.
    destino = _destino_seguro(
        diretorio_repositorio,
        caminho_relativo,
    )

    # -----------------------------------------
    # Criar arquivo novo
    # -----------------------------------------

    if not sobrescrever:
        try:
            with destino.open(
                "x",
                encoding="utf-8",
                newline="\n",
            ) as arquivo:
                arquivo.write(conteudo)

        except FileExistsError as erro:
            raise RuntimeError(
                f"Arquivo já existe: {caminho_relativo}"
            ) from erro

        return destino

    # -----------------------------------------
    # Sobrescrever arquivo existente
    # -----------------------------------------

    if not destino.is_file():
        raise RuntimeError(
            "Arquivo para sobrescrita "
            "não encontrado."
        )

    conteudo_atual = destino.read_text(
        encoding="utf-8"
    )

    if conteudo_atual != conteudo_esperado:
        raise RuntimeError(
            "Arquivo mudou desde a revisão; "
            "alteração cancelada."
        )

    # Preparar conteúdo em arquivo temporário,
    # na mesma pasta do destino.
    descritor, temporario = tempfile.mkstemp(
        prefix=".agente-",
        suffix=".tmp",
        dir=destino.parent,
    )

    try:
        with os.fdopen(
            descritor,
            "w",
            encoding="utf-8",
            newline="\n",
        ) as arquivo:
            arquivo.write(conteudo)

        # Revalidar o caminho e o conteúdo
        # imediatamente antes da substituição.
        destino = _destino_seguro(
            diretorio_repositorio,
            caminho_relativo,
        )

        if (
            not destino.is_file()
            or destino.read_text(
                encoding="utf-8"
            ) != conteudo_esperado
        ):
            raise RuntimeError(
                "Arquivo mudou antes da escrita; "
                "alteração cancelada."
            )

        os.replace(
            temporario,
            destino,
        )

    finally:
        if os.path.exists(temporario):
            os.unlink(temporario)

    return destino

def obter_diff_git(diretorio_repositorio):
    """
    Mostra as alterações locais realizadas
    no repositório.
    """

    return executar_comando(
        [
            "git",
            "diff",
            "--no-ext-diff",
        ],
        diretorio=diretorio_repositorio,
    )

def listar_arquivos_nao_rastreados(diretorio_repositorio):
    """
    Lista arquivos novos que ainda não estão sendo
    rastreados pelo Git.
    """

    resultado = executar_comando(
        [
            "git",
            "ls-files",
            "--others",
            "--exclude-standard",
        ],
        diretorio=diretorio_repositorio,
    )

    if not resultado:
        return []

    return [
        linha.strip()
        for linha in resultado.splitlines()
        if linha.strip()
    ]

def obter_revisao_local(diretorio_repositorio):
    """
    Gera uma revisão das alterações locais antes
    de qualquer commit.
    """

    raiz = Path(diretorio_repositorio).resolve()

    revisao = {
        "diff": obter_diff_git(diretorio_repositorio),
        "arquivos_novos": [],
    }

    arquivos_novos = listar_arquivos_nao_rastreados(
        diretorio_repositorio
    )

    for caminho_relativo in arquivos_novos:
        caminho = (raiz / caminho_relativo).resolve()

        try:
            caminho.relative_to(raiz)

        except ValueError:
            continue

        try:
            conteudo = caminho.read_text(
                encoding="utf-8"
            )

        except (UnicodeDecodeError, OSError):
            conteudo = "[Arquivo não textual]"

        revisao["arquivos_novos"].append({
            "caminho": caminho_relativo,
            "conteudo": conteudo,
        })

    return revisao

def adicionar_arquivo_stage(
    diretorio_repositorio,
    caminho_relativo,
):
    """
    Adiciona um arquivo específico à área de staging.

    Não realiza commit nem push.
    """

    raiz = Path(diretorio_repositorio).resolve()
    arquivo = (raiz / caminho_relativo).resolve()

    try:
        arquivo.relative_to(raiz)

    except ValueError as erro:
        raise RuntimeError(
            "Tentativa de acessar arquivo fora "
            "do repositório autorizado."
        ) from erro

    if not arquivo.exists():
        raise RuntimeError(
            f"O arquivo '{caminho_relativo}' não existe."
        )

    executar_comando(
        [
            "git",
            "add",
            "--",
            caminho_relativo,
        ],
        diretorio=diretorio_repositorio,
    )

def obter_diff_stage(diretorio_repositorio):
    """
    Mostra exatamente o conteúdo preparado
    para o próximo commit.
    """

    return executar_comando(
        [
            "git",
            "diff",
            "--cached",
            "--no-ext-diff",
        ],
        diretorio=diretorio_repositorio,
    )

def remover_arquivo_stage(
    diretorio_repositorio,
    caminho_relativo,
):
    """
    Remove um arquivo da área de staging,
    mantendo o arquivo no disco.
    """

    executar_comando(
        [
            "git",
            "restore",
            "--staged",
            "--",
            caminho_relativo,
        ],
        diretorio=diretorio_repositorio,
    )

def criar_commit_local(
    diretorio_repositorio,
    mensagem,
):
    """
    Cria um commit somente no repositório local.

    Não executa push.
    """

    if not mensagem or not mensagem.strip():
        raise ValueError(
            "A mensagem do commit não pode estar vazia."
        )

    return executar_comando(
        [
            "git",
            "commit",
            "-m",
            mensagem.strip(),
        ],
        diretorio=diretorio_repositorio,
    )

def atualizar_referencia_remota(
    diretorio_repositorio,
    branch,
):
    """
    Atualiza somente a referência local da branch remota.

    Não modifica o GitHub remoto.
    """

    executar_comando(
        [
            "git",
            "fetch",
            "origin",
            branch,
        ],
        diretorio=diretorio_repositorio,
        timeout=120,
    )

def obter_commits_para_push(
    diretorio_repositorio,
    branch,
):
    """
    Retorna os commits locais que ainda não existem
    na branch remota.
    """

    return executar_comando(
        [
            "git",
            "log",
            f"origin/{branch}..HEAD",
            "--oneline",
        ],
        diretorio=diretorio_repositorio,
    )

def obter_sincronizacao(
    diretorio_repositorio,
    branch,
):
    """
    Informa quantos commits a branch local está
    atrás e à frente da branch remota.
    """

    resultado = executar_comando(
        [
            "git",
            "rev-list",
            "--left-right",
            "--count",
            f"origin/{branch}...HEAD",
        ],
        diretorio=diretorio_repositorio,
    )

    partes = resultado.split()

    if len(partes) != 2:
        raise RuntimeError(
            "Não foi possível determinar o estado "
            "de sincronização."
        )

    atras = int(partes[0])
    frente = int(partes[1])

    return {
        "atras": atras,
        "frente": frente,
    }

def obter_branch_atual(diretorio_repositorio):
    """
    Retorna a branch atualmente selecionada.
    """

    return executar_comando(
        [
            "git",
            "branch",
            "--show-current",
        ],
        diretorio=diretorio_repositorio,
    )

def executar_push(
    diretorio_repositorio,
    branch,
):
    """
    Publica a branch local no origin.

    Esta função deve ser chamada somente
    após aprovação explícita do usuário.
    """

    return executar_comando(
        [
            "git",
            "push",
            "origin",
            branch,
        ],
        diretorio=diretorio_repositorio,
        timeout=120,
    )

def atualizar_todas_referencias(diretorio_repositorio):
    """
    Atualiza as referências remotas sem alterar
    os arquivos locais.
    """

    executar_comando(
        [
            "git",
            "fetch",
            "--all",
            "--prune",
        ],
        diretorio=diretorio_repositorio,
        timeout=120,
    )

def obter_merge_base(
    diretorio_repositorio,
    branch_a,
    branch_b,
):
    """
    Descobre se duas branches possuem
    um ancestral comum.
    """

    try:
        return executar_comando(
            [
                "git",
                "merge-base",
                branch_a,
                branch_b,
            ],
            diretorio=diretorio_repositorio,
        )

    except RuntimeError:
        return None

def obter_commits_exclusivos(
    diretorio_repositorio,
    branch_a,
    branch_b,
):
    """
    Retorna commits exclusivos de cada branch.
    """

    somente_a = executar_comando(
        [
            "git",
            "log",
            "--oneline",
            f"{branch_b}..{branch_a}",
        ],
        diretorio=diretorio_repositorio,
    )

    somente_b = executar_comando(
        [
            "git",
            "log",
            "--oneline",
            f"{branch_a}..{branch_b}",
        ],
        diretorio=diretorio_repositorio,
    )

    return {
        branch_a: somente_a,
        branch_b: somente_b,
    }

def branch_remota_existe(
    diretorio_repositorio,
    branch,
):
    """
    Verifica se uma branch já existe no origin.
    """

    resultado = executar_comando(
        [
            "git",
            "ls-remote",
            "--heads",
            "origin",
            branch,
        ],
        diretorio=diretorio_repositorio,
    )

    return bool(resultado.strip())

def publicar_nova_branch(
    diretorio_repositorio,
    branch,
):
    """
    Publica uma branch local nova no origin
    e configura o upstream.

    Deve ser chamada somente após aprovação.
    """

    return executar_comando(
        [
            "git",
            "push",
            "--set-upstream",
            "origin",
            branch,
        ],
        diretorio=diretorio_repositorio,
        timeout=120,
    )

def obter_hash_ref(
    diretorio_repositorio,
    referencia,
):
    """
    Retorna o hash de uma referência Git.
    """

    return executar_comando(
        [
            "git",
            "rev-parse",
            referencia,
        ],
        diretorio=diretorio_repositorio,
    )

def obter_arquivos_diferentes(
    diretorio_repositorio,
    referencia_origem,
    referencia_destino,
):
    """
    Mostra os arquivos que diferem entre
    duas referências.
    """

    return executar_comando(
        [
            "git",
            "diff",
            "--name-status",
            f"{referencia_origem}..{referencia_destino}",
        ],
        diretorio=diretorio_repositorio,
    )

def atualizar_branch_remota(
    diretorio_repositorio,
    branch_origem,
    branch_destino,
):
    """
    Envia uma branch local para outra branch remota.

    Não utiliza force push.
    """

    return executar_comando(
        [
            "git",
            "push",
            "origin",
            f"{branch_origem}:{branch_destino}",
        ],
        diretorio=diretorio_repositorio,
        timeout=120,
    )

def branch_e_ancestral(
    diretorio_repositorio,
    branch_origem,
    branch_destino,
):
    """
    Verifica se todo o histórico da branch_origem
    está contido na branch_destino.
    """

    resultado = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            branch_origem,
            branch_destino,
        ],
        cwd=diretorio_repositorio,
        capture_output=True,
        text=True,
    )

    return resultado.returncode == 0

def excluir_branch_remota(
    diretorio_repositorio,
    branch,
):
    """
    Exclui uma branch do origin.

    Deve ser chamada somente após aprovação explícita.
    """

    return executar_comando(
        [
            "git",
            "push",
            "origin",
            "--delete",
            branch,
        ],
        diretorio=diretorio_repositorio,
        timeout=120,
    )

def atualizar_main_local(
    diretorio_repositorio,
):
    """
    Atualiza a branch main local exclusivamente
    por fast-forward.
    """

    executar_comando(
        [
            "git",
            "switch",
            "main",
        ],
        diretorio=diretorio_repositorio,
    )

    executar_comando(
        [
            "git",
            "merge",
            "--ff-only",
            "origin/main",
        ],
        diretorio=diretorio_repositorio,
    )

def excluir_branch_local(
    diretorio_repositorio,
    branch,
):
    """
    Exclui uma branch local usando -d.

    O Git recusará se ela não estiver integrada.
    """

    return executar_comando(
        [
            "git",
            "branch",
            "-d",
            branch,
        ],
        diretorio=diretorio_repositorio,
    )

def listar_arquivos_stage(diretorio_repositorio):
    """
    Lista arquivos que já estão preparados
    na área de staging.
    """

    resultado = executar_comando(
        [
            "git",
            "diff",
            "--cached",
            "--name-only",
        ],
        diretorio=diretorio_repositorio,
    )

    if not resultado:
        return []

    return [
        linha.strip()
        for linha in resultado.splitlines()
        if linha.strip()
    ]

def listar_arquivos_para_commit(diretorio_repositorio):
    """
    Localiza arquivos modificados, removidos
    ou novos que ainda não estão no staging.
    """

    modificados = executar_comando(
        [
            "git",
            "diff",
            "--name-only",
        ],
        diretorio=diretorio_repositorio,
    )

    novos = executar_comando(
        [
            "git",
            "ls-files",
            "--others",
            "--exclude-standard",
        ],
        diretorio=diretorio_repositorio,
    )

    arquivos = set()

    if modificados:
        arquivos.update(
            linha.strip()
            for linha in modificados.splitlines()
            if linha.strip()
        )

    if novos:
        arquivos.update(
            linha.strip()
            for linha in novos.splitlines()
            if linha.strip()
        )

    return sorted(arquivos)

def adicionar_caminho_stage(
    diretorio_repositorio,
    caminho_relativo,
):
    """
    Coloca um caminho específico no staging.

    Também funciona para arquivos removidos.
    """

    raiz = Path(
        diretorio_repositorio
    ).resolve()

    destino = (
        raiz / caminho_relativo
    ).resolve()

    try:
        destino.relative_to(raiz)

    except ValueError as erro:
        raise RuntimeError(
            "Caminho fora do repositório autorizado."
        ) from erro

    executar_comando(
        [
            "git",
            "add",
            "--",
            caminho_relativo,
        ],
        diretorio=diretorio_repositorio,
    )

def remover_caminho_stage(
    diretorio_repositorio,
    caminho_relativo,
):
    """
    Remove um caminho do staging sem apagar
    a alteração do disco.
    """

    executar_comando(
        [
            "git",
            "restore",
            "--staged",
            "--",
            caminho_relativo,
        ],
        diretorio=diretorio_repositorio,
    )

def obter_historico_recente(
    diretorio_repositorio,
    limite=10,
):
    """
    Retorna os commits mais recentes da branch atual.
    """

    if limite < 1:
        raise ValueError(
            "O limite deve ser maior que zero."
        )

    return executar_comando(
        [
            "git",
            "log",
            "--oneline",
            f"-{limite}",
        ],
        diretorio=diretorio_repositorio,
    )

def atualizar_branch_local_ff(
    diretorio_repositorio,
    branch,
):
    """
    Atualiza a branch local usando somente
    fast-forward.

    Nunca cria merge automático.
    """

    executar_comando(
        [
            "git",
            "merge",
            "--ff-only",
            f"origin/{branch}",
        ],
        diretorio=diretorio_repositorio,
    )

def mover_arquivo_git(
    diretorio_repositorio,
    origem,
    destino,
):
    """
    Move um arquivo dentro do repositório
    utilizando git mv.

    Origem e destino são validados para impedir
    caminhos fora do workspace do repositório.
    """

    raiz = Path(
        diretorio_repositorio
    ).resolve()

    origem_local = (
        raiz / origem
    ).resolve()

    destino_local = (
        raiz / destino
    ).resolve()

    try:
        origem_local.relative_to(
            raiz
        )

        destino_local.relative_to(
            raiz
        )

    except ValueError as erro:
        raise RuntimeError(
            "Movimento fora do repositório "
            "foi bloqueado."
        ) from erro

    if not origem_local.is_file():
        raise RuntimeError(
            f"Arquivo de origem não encontrado: "
            f"{origem}"
        )

    if destino_local.exists():
        raise RuntimeError(
            f"Destino já existe: {destino}"
        )

    destino_local.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    executar_comando(
        [
            "git",
            "mv",
            "--",
            origem,
            destino,
        ],
        diretorio=diretorio_repositorio,
    )
    
def mover_arquivo_local_sem_stage(
    diretorio_repositorio,
    origem,
    destino,
):
    """
    Move um arquivo Java sem adicionar alterações
    ao staging do Git.

    Nesta versão, permite somente:
    src/Arquivo.java
    ->
    src/main/java/Arquivo.java
    """

    from pathlib import PurePosixPath

    origem_rel = PurePosixPath(origem)
    destino_rel = PurePosixPath(destino)

    # Impedir caminhos absolutos, travessias
    # de diretório e barras incompatíveis.
    if (
        origem_rel.is_absolute()
        or destino_rel.is_absolute()
        or ".." in origem_rel.parts
        or ".." in destino_rel.parts
        or "\\" in origem
        or "\\" in destino
    ):
        raise RuntimeError(
            "Caminho de movimentação inválido."
        )

    # Permitir somente o movimento específico
    # que implementamos para estrutura Maven.
    destino_esperado = (
        PurePosixPath("src/main/java")
        / origem_rel.name
    )

    if (
        len(origem_rel.parts) != 2
        or origem_rel.parts[0] != "src"
        or origem_rel.suffix.lower() != ".java"
        or destino_rel != destino_esperado
    ):
        raise RuntimeError(
            "Movimento não permitido pela política."
        )

    raiz = Path(diretorio_repositorio).resolve()

    origem_bruta = raiz.joinpath(
        *origem_rel.parts
    )

    destino_bruto = raiz.joinpath(
        *destino_rel.parts
    )

    origem_local = origem_bruta.resolve()
    destino_local = destino_bruto.resolve()

    try:
        origem_local.relative_to(raiz)
        destino_local.relative_to(raiz)

    except ValueError as erro:
        raise RuntimeError(
            "Movimento fora do repositório."
        ) from erro

    if origem_bruta.is_symlink():
        raise RuntimeError(
            "Origem simbólica não permitida."
        )

    if not origem_local.is_file():
        raise RuntimeError(
            f"Arquivo não encontrado: {origem}"
        )

    if (
        destino_bruto.exists()
        or destino_bruto.is_symlink()
    ):
        raise RuntimeError(
            f"Destino já existe: {destino}"
        )

    destino_local.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Movimentação pelo Python.
    # Não executa git add nem git mv.
    origem_local.rename(destino_local)

    return {
        "origem": origem,
        "destino": destino,
    }

def obter_head_commit(diretorio_repositorio):
    """
    Retorna o SHA do commit apontado por HEAD.

    Consulta somente o repositório local.
    Não modifica arquivos nem o Git.
    """

    import subprocess

    resultado = subprocess.run(
        [
            "git",
            "-C",
            str(diretorio_repositorio),
            "rev-parse",
            "--verify",
            "HEAD",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return resultado.stdout.strip()

def validar_destino_origin(
    diretorio_repositorio,
    nome_completo,
):
    """
    Confirma que origin corresponde exatamente
    ao repositório GitHub autorizado.

    Aceita:
    - HTTPS
    - SSH no formato git@github.com
    - SSH no formato ssh://git@github.com

    Bloqueia:
    - outros hosts;
    - outros repositórios;
    - destinos de push múltiplos;
    - ausência de origin.

    Não realiza push.
    """

    import re
    import subprocess

    padrao_nome = (
        r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+"
    )

    if (
        not isinstance(nome_completo, str)
        or not re.fullmatch(
            padrao_nome,
            nome_completo,
        )
    ):
        raise RuntimeError(
            "Nome do repositório inválido."
        )

    def identificar_repositorio(url):
        url = url.strip()

        padrao_url = (
            r"(?:"
            r"https://github\.com/"
            r"|git@github\.com:"
            r"|ssh://git@github\.com/"
            r")"
            r"([A-Za-z0-9-]+)"
            r"/"
            r"([A-Za-z0-9_.-]+)"
        )

        encontrado = re.fullmatch(
            padrao_url,
            url,
            flags=re.IGNORECASE,
        )

        if encontrado is None:
            raise RuntimeError(
                "URL remota não permitida: "
                "esperado um repositório github.com."
            )

        proprietario = encontrado.group(1)
        repositorio = encontrado.group(2)

        if repositorio.lower().endswith(".git"):
            repositorio = repositorio[:-4]

        if not repositorio:
            raise RuntimeError(
                "Nome de repositório remoto inválido."
            )

        return (
            f"{proprietario}/{repositorio}"
        ).casefold()

    def consultar_urls(push=False):
        comando = [
            "git",
            "-C",
            str(diretorio_repositorio),
            "remote",
            "get-url",
        ]

        if push:
            comando.append("--push")

        comando.extend([
            "--all",
            "origin",
        ])

        try:
            resultado = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

        except (
            OSError,
            subprocess.TimeoutExpired,
        ) as erro:
            raise RuntimeError(
                "Não foi possível consultar origin."
            ) from erro

        if resultado.returncode != 0:
            raise RuntimeError(
                "Remoto origin não encontrado "
                "ou inválido."
            )

        urls = [
            linha.strip()
            for linha in resultado.stdout.splitlines()
            if linha.strip()
        ]

        if len(urls) != 1:
            raise RuntimeError(
                "Origin possui múltiplos destinos "
                "ou uma configuração ambígua."
            )

        return urls[0]

    esperado = nome_completo.casefold()

    # Verificar URL utilizada para consultas.
    url_fetch = consultar_urls(
        push=False
    )

    # Verificar URL efetiva utilizada pelo push.
    # Ela pode ser diferente da URL de fetch.
    url_push = consultar_urls(
        push=True
    )

    for url in (url_fetch, url_push):

        identificado = identificar_repositorio(
            url
        )

        if identificado != esperado:
            raise RuntimeError(
                "Destino remoto incompatível "
                "com o repositório autorizado."
            )

    return True
