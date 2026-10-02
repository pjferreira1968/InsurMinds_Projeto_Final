# ========================
# InsurMinds_Projeto_Final
# ========================

InsurMinds_Projeto_Final é um produto da **IA4Seg** para análise e comparação de apólices D&O com OCR, IA Generativa, persistência e relatórios.

## Problema resolvido

Apólices D&O são extensas, jurídicas e difíceis de comparar manualmente. O InsurMinds_Projeto_Final reduz o esforço inicial de triagem ao estruturar informações, evidências e diferenças relevantes.

## Funcionalidades

- Upload de PDF e imagens.
- Validação de extensão, MIME type, tamanho e duplicidade de conteúdo.
- Extração de texto nativo de PDF e OCR local com Tesseract para imagens.
- LLM configurável entre Ollama e OpenAI.
- Persistência com SQLAlchemy, SQLite por padrão e PostgreSQL como opção.
- Consulta, exclusão e comparação de apólices.
- Comparação Completa ou Relevante com critérios configuráveis.
- Logs numerados de importação e comparação.
- Relatório de comparação em PDF orientado ao negócio.
- Interface web Streamlit e API FastAPI.

## Pré-requisitos

- Python 3.11 ou superior.
- Tesseract OCR com idioma português instalado para OCR de imagens.
- Ollama local com o modelo configurado para extração por LLM.
- Chave OpenAI apenas quando esse provedor alternativo for utilizado.

## Instalação padrão com SQLite

SQLite é o banco padrão. Ele grava os dados em
`data/insurminds_projeto_final.sqlite` e não exige WSL, Docker ou instalação de
um servidor de banco de dados.

Execute os comandos abaixo no PowerShell, a partir do diretório que contém a
pasta do projeto:

```powershell
cd InsurMinds_Projeto_Final
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
Copy-Item .env.example .env
python scripts\inicializar_banco.py
```

A mensagem de sucesso da inicialização deve listar as tabelas 
`apolices`, `comparacoes` e `documentos`.

Em Linux ou macOS, os comandos equivalentes para ativar o ambiente e copiar a
configuração são:

```bash
source .venv/bin/activate
cp .env.example .env
python scripts/inicializar_banco.py
```

O valor padrão já está presente em `.env.example` e no código:

```dotenv
DATABASE_URL=sqlite:///./data/insurminds_projeto_final.sqlite
```

## =========
## Tesseract
## =========

O pacote Python `pytesseract`, instalado por `requirements.txt`, é apenas a integração com o OCR. O executável do Tesseract e os dados do idioma português também precisam ser instalados no sistema operacional.

### Windows

Instale o Tesseract pelo Windows Package Manager:

```powershell
winget install -e --id UB-Mannheim.TesseractOCR
```

Feche e abra o PowerShell após a instalação. Confirme o executável usando o
caminho padrão:

```powershell
& "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
& "C:\Program Files\Tesseract-OCR\tesseract.exe" --list-langs
```

A lista de idiomas precisa conter `por`. Se ele não aparecer, abra o PowerShell
como administrador e baixe o modelo oficial `tessdata_fast` para a instalação:

```powershell
$TesseractExe = "C:\Program Files\Tesseract-OCR\tesseract.exe"
if (-not (Test-Path $TesseractExe)) {
    throw "Tesseract não encontrado em $TesseractExe"
}
$Tessdata = Join-Path (Split-Path $TesseractExe) "tessdata"
New-Item -ItemType Directory -Force -Path $Tessdata | Out-Null
Invoke-WebRequest `
    -Uri "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/por.traineddata" `
    -OutFile (Join-Path $Tessdata "por.traineddata")
& $TesseractExe --list-langs
```

O arquivo instalado deve ser
`C:\Program Files\Tesseract-OCR\tessdata\por.traineddata`. O modelo utilizado é
o arquivo oficial de português mantido pelo projeto
[tesseract-ocr/tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast/blob/main/por.traineddata).

Também é possível usar o instalador do projeto UB Mannheim e selecionar
**Portuguese** em `Additional language data` durante a instalação.

No Windows, preencha o arquivo `.env` do projeto desta forma:

```dotenv
OCR_PROVIDER=auto
OCR_LANGUAGE=por
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

Não execute essas três linhas diretamente no PowerShell. O projeto lê o arquivo `.env` automaticamente. Para substituir os valores apenas na sessão atual do PowerShell, use a sintaxe `$env:NOME = "valor"`:

```powershell
$env:OCR_PROVIDER = "auto"
$env:OCR_LANGUAGE = "por"
$env:TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

Portanto, `OCR_PROVIDER=auto` pertence ao arquivo `.env`. Quando digitado diretamente no PowerShell, ele produz `CommandNotFoundException`; nesse terminal, a forma correta é `$env:OCR_PROVIDER = "auto"`.

Se o PowerShell informar que `tesseract` não é reconhecido, o projeto ainda
conseguirá usar o caminho definido em `TESSERACT_CMD`. Para disponibilizar o
comando em novos terminais, acrescente o diretório ao `Path` do usuário:

```powershell
$PastaTesseract = "C:\Program Files\Tesseract-OCR"
$PathUsuario = [Environment]::GetEnvironmentVariable("Path", "User")
if (($PathUsuario -split ";") -notcontains $PastaTesseract) {
    [Environment]::SetEnvironmentVariable(
        "Path",
        ($PathUsuario.TrimEnd(";") + ";" + $PastaTesseract),
        "User"
    )
}
```

Feche e abra o PowerShell e confira novamente:

```powershell
tesseract --version
tesseract --list-langs
```

### Ubuntu e Debian

```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-por
```

Normalmente não é necessário definir `TESSERACT_CMD`, pois o executável é instalado no `PATH`.

### macOS

Com Homebrew:

```bash
brew install tesseract tesseract-lang
```

### Verificação

Confirme a instalação e a disponibilidade do idioma português:

```bash
tesseract --version
tesseract --list-langs
```

A saída de `tesseract --list-langs` deve conter `por`.

O MVP aplica OCR do Tesseract a arquivos de imagem. PDFs que já possuem camada de texto são lidos diretamente; OCR de PDFs digitalizados é uma limitação conhecida desta versão.

## ------
## Ollama
## ------

O Ollama e o modelo configurado são pré-requisitos para a extração local por IA.
No Windows 10 ou posterior, instale pelo PowerShell usando o comando oficial:

```powershell
irm https://ollama.com/install.ps1 | iex
```

Também é possível baixar o instalador em
[ollama.com/download/windows](https://ollama.com/download/windows). Feche e abra
o PowerShell depois da instalação e confirme:

```powershell
ollama --version
```

O instalador do Windows inicia o Ollama em segundo plano e disponibiliza a API
em `http://localhost:11434`. Baixe o modelo configurado pela aplicação:

```powershell
ollama pull llama3.1:8b
ollama list
Invoke-RestMethod http://localhost:11434/api/tags
```

Se a API não responder, inicie o servidor manualmente e mantenha o terminal
aberto:

```powershell
ollama serve
```

No Linux, a instalação oficial pode ser feita com:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b
```

Confira estas definições no `.env`:

```dotenv
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_TIMEOUT_SECONDS=900
OLLAMA_KEEP_ALIVE=30m
```

Extrações estruturadas de apólices extensas podem levar vários minutos em CPU.
`OLLAMA_TIMEOUT_SECONDS` controla somente o tempo de leitura do Ollama; o padrão
de 600 segundos acomoda a primeira análise sem aumentar o timeout da OpenAI.
`OLLAMA_KEEP_ALIVE` mantém o modelo carregado entre importações. Depois de alterar
esses valores, interrompa a aplicação com `Ctrl+C` e inicie o Streamlit novamente.

Se o console mostrar `timed out`, confirme primeiro que o modelo responde e, em
hardware mais lento, aumente o valor no `.env`, por exemplo:

```dotenv
OLLAMA_TIMEOUT_SECONDS=900
```

A documentação oficial do Ollama para Windows está disponível em
[docs.ollama.com/windows](https://docs.ollama.com/windows).

## OpenAI

OpenAI permanece como provedor alternativo. Para utilizá-lo, defina
`LLM_PROVIDER=openai`, `OPENAI_API_KEY` e `OPENAI_MODEL`. Não grave chaves em
commits. A instalação básica do produto continua validando Tesseract e Ollama.

## Validação obrigatória do ambiente

Execute a validação somente depois de instalar o Tesseract, confirmar o idioma
`por`, instalar o Ollama e baixar `llama3.1:8b`:

```powershell
python scripts\validar_ambiente.py
```

O script retorna código de erro quando algum requisito não estiver pronto. Ele
verifica:

- bibliotecas Python;
- conexão com o banco SQLite padrão ou com a URL configurada;
- executável do Tesseract e disponibilidade do idioma definido em `OCR_LANGUAGE`;
- executável e API local do Ollama;
- presença do modelo definido em `OLLAMA_MODEL`.

Somente prossiga para a execução quando todos os itens forem apresentados como
`ok`.

## Execução

Como o projeto foi instalado em modo editável durante a instalação, não é
necessário definir `PYTHONPATH`. Execute os comandos a partir da raiz do projeto.

API:

```powershell
python -m insurminds_projeto_final.main
```

Interface:

```powershell
streamlit run src/insurminds_projeto_final/ui/app.py
```

Se optar por não instalar o projeto com `pip install -e .`, defina
`$env:PYTHONPATH = "src"` no PowerShell, `export PYTHONPATH=src` no Linux ou
macOS, ou `set PYTHONPATH=src` no Prompt de Comando clássico do Windows.

## Operação

Na importação, o log da interface apresenta as etapas de validação, armazenamento, extração, estruturação e persistência. Cada linha informa a classe ou função e o método Python em execução no formato `[Objeto.metodo]`. Se já existir um documento com o mesmo nome, a versão anterior, sua apólice estruturada, suas comparações e seus relatórios derivados são removidos antes do registro da nova versão.

A guia **Apólices importadas** possui um grid com seleção por linha. Marque uma ou mais apólices, pressione **Excluir selecionadas** e confirme a operação para remover os arquivos, dados estruturados, comparações e relatórios relacionados.

Na comparação, selecione claramente a apólice A e a apólice B e escolha um dos modos:

- **C Completa:** compara todos os campos estruturados disponíveis.
- **R Relevante:** permite selecionar os pontos de negócio previamente parametrizados em `config/pontos_relevantes.json`. Todos são selecionados inicialmente, mas o usuário pode manter somente os critérios desejados. É obrigatório selecionar ao menos um ponto relevante.

No modo Relevante, cada ponto possui um `peso` editável de 1 a 10 e uma
`regra_avaliacao`. Limites maiores e franquias menores recebem vantagem objetiva;
coberturas contratadas também podem pontuar. Para ajustar a importância de um
critério, altere somente seu campo `peso` no JSON. Valores financeiros usam os
maiores pesos por padrão. O parecer ponderado e as pontuações são apresentados
na interface e no relatório PDF, sempre sujeitos à revisão especializada.

A seleção dos pontos relevantes é mantida durante a sessão. Ao alterá-la, o
resultado anterior é descartado para evitar a exibição de uma comparação
desatualizada. O quadro comparativo, as pontuações, o parecer e o relatório PDF
consideram exclusivamente os pontos selecionados. A mesma validação de ao menos
um ponto é aplicada pela interface, pelo serviço e pela API.

Quando um ponto selecionado não possui correspondência nos dados extraídos de
nenhuma das apólices, ele permanece no quadro comparativo com a classificação
**Não encontrado**. Esse estado também é destacado na interface e no relatório
PDF, sem atribuir pontuação ou vantagem a qualquer apólice.

Valores financeiros e moedas são comparados em critérios separados. Assim, uma diferença de limite ou franquia não é apresentada como diferença de moeda quando ambas as apólices utilizam BRL. Novos pontos relevantes podem ser acrescentados ao arquivo JSON por categoria e palavras-chave, sem alteração no código Python. O resultado é mostrado em linguagem de negócio e pode ser baixado em PDF.

## Documentação técnica

A documentação de apoio está em `./Projeto_Final_Artefatos`. 


## Organização dos diretórios

- `InsurMinds_Projeto_Final`: somente aplicação principal, configuração, persistência local e arquivos de implantação.
- `InsurMinds_Projeto_Final/scripts`: scripts necessários à instalação, inicialização do banco e validação do ambiente.
- `InsurMinds_Projeto_Final_Artefatos/Relatorio_Tecnico_InsurMinds_Projeto_Final.pdf`: relatório técnico com diagrama de objetos Python.
- `InsurMinds_Projeto_Final_Artefatos/IA4Seg_InsurMinds_Projeto_Final_Apresentacao.pptx`: apresentação funcional e técnica.
- `InsurMinds_Projeto_Final_Artefatos/IA4Seg_InsurMinds_Projeto_Final_Tutorial.mp4`: tutorial real de importação e comparação.


## ===================
## PostgreSQL opcional
## ===================

Esta seção é opcional e pode ser seguida depois que a instalação padrão com
SQLite, Tesseract e Ollama estiver funcionando. PostgreSQL exige Docker Desktop
e Docker Compose no Windows.

### 1. Verificar ou atualizar o WSL

Abra o PowerShell como administrador:

```powershell
wsl --status
wsl --version
wsl -l -v
```

Se o WSL não estiver instalado, instale-o e reinicie o Windows quando solicitado:

```powershell
wsl --install
```

Para atualizar uma instalação existente e usar WSL 2:

```powershell
wsl --update
wsl --set-default-version 2
wsl --shutdown
```

Quando a Microsoft Store estiver bloqueada, tente:

```powershell
wsl --update --web-download
```

Consulte a documentação oficial da Microsoft sobre
[instalação do WSL](https://learn.microsoft.com/windows/wsl/install) e
[comandos do WSL](https://learn.microsoft.com/windows/wsl/basic-commands).

### 2. Instalar o Docker Desktop

Baixe o instalador em
[Docker Desktop para Windows](https://docs.docker.com/desktop/setup/install/windows-install/)
ou use:

```powershell
winget install -e --id Docker.DockerDesktop
```

Mantenha selecionado o mecanismo WSL 2. Inicie o Docker Desktop, aguarde o
Docker Engine e abra um novo PowerShell:

```powershell
docker --version
docker compose version
docker info
```

O Docker Desktop já inclui o Compose. Se `docker info` não acessar o daemon,
confirme que o Docker Desktop está aberto e concluiu a inicialização.

### 3. Iniciar e preparar o PostgreSQL

Execute na raiz do projeto com `.venv` ativado:

```powershell
cd C:\caminho\para\InsurMinds_Projeto_Final
.\.venv\Scripts\Activate.ps1
Copy-Item .env.postgres.example .env -Force
docker compose up -d postgres
docker compose ps
```

O serviço deve ficar `healthy`. Em caso de falha:

```powershell
docker compose logs postgres
Test-NetConnection localhost -Port 5432
```

Crie ou confira as tabelas e valide novamente todo o ambiente:

```powershell
python scripts\inicializar_banco.py --aguardar-segundos 60
python scripts\validar_ambiente.py
```

Também é possível informar a URL somente nessa execução:

```powershell
python scripts\inicializar_banco.py --database-url "postgresql+psycopg://insurminds_projeto_final:insurminds_projeto_final@localhost:5432/insurminds_projeto_final" --aguardar-segundos 60
```

Para executar também a API em contêiner:

```powershell
docker compose up -d --build
docker compose ps
```

A API fica disponível em `http://localhost:8000/docs`. Para interromper os
contêineres sem apagar o banco, use `docker compose down`. O comando
`docker compose down -v` remove o volume e **apaga os dados do PostgreSQL**.

### Diagnóstico do PostgreSQL

- `connection refused`: aguarde `healthy` e consulte `docker compose logs postgres`.
- `password authentication failed`: recopie `.env.postgres.example` ou alinhe as credenciais com `docker-compose.yml`.
- Porta `5432` ocupada: interrompa a outra instância ou altere a porta publicada e a `DATABASE_URL`.
- `ModuleNotFoundError`: ative `.venv` e execute `python -m pip install -e . --no-deps`.
- Script não encontrado: execute `Test-Path .\scripts\inicializar_banco.py` na raiz do projeto.

## Limitações conhecidas

OCR pode falhar em documentos de baixa qualidade. LLMs podem interpretar cláusulas ambíguas de forma equivocada. O MVP não substitui corretores, subscritores, advogados, reguladores ou especialistas em seguros.

## Responsável pelo produto

IA4Seg

## Licença

Distribuído sob licença MIT. Consulte `LICENSE`.
