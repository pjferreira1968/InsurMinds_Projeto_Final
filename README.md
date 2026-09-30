# PfCompara

PfCompara é um produto da **IA4Seg** para análise e comparação de apólices D&O com OCR, IA Generativa, persistência e relatórios.

## Problema resolvido

Apólices D&O são extensas, jurídicas e difíceis de comparar manualmente. O PfCompara reduz o esforço inicial de triagem ao estruturar informações, evidências e diferenças relevantes.

## Funcionalidades

- Upload de PDF e imagens.
- Validação de extensão, MIME type, tamanho e duplicidade de conteúdo.
- Extração de texto nativo de PDF e OCR local com Tesseract para imagens.
- LLM configurável entre Ollama e OpenAI.
- Persistência com SQLAlchemy e PostgreSQL.
- Consulta, exclusão e comparação de apólices.
- Comparação Completa ou Relevante com critérios configuráveis.
- Logs numerados de importação e comparação.
- Relatório de comparação em PDF orientado ao negócio.
- Interface web Streamlit e API FastAPI.

## Pré-requisitos

- Python 3.11 ou superior.
- Docker e Docker Compose para PostgreSQL ou sqllite (Execução local).
- Tesseract OCR com idioma português instalado para OCR de imagens.
- Ollama local ou chave OpenAI para extração por LLM.

## Instalação

```bash
git clone https://github.com/pjferreira1968/InsurMinds_Projeto_Final.git PfCompara
cd PfCompara
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Em Linux ou macOS, use `source .venv/bin/activate` e `cp .env.example .env`.
Ao usar **Download ZIP** no GitHub, renomeie a pasta extraída para `PfCompara` antes de executar os comandos.

## PostgreSQL

```bash
docker compose up -d postgres
python ..\PfCompara_Apoio\ferramentas\inicializar_banco.py
```

Para execução local sem PostgreSQL, ajuste `DATABASE_URL=sqlite:///./data/pfcompara.sqlite` no `.env`.

## Tesseract

O pacote Python `pytesseract`, instalado por `requirements.txt`, é apenas a integração com o OCR. O executável do Tesseract e os dados do idioma português também precisam ser instalados no sistema operacional.

### Windows

Instale pelo Windows Package Manager:

```powershell
winget install --id UB-Mannheim.TesseractOCR
```

Também é possível usar o instalador do projeto UB Mannheim. Durante a instalação, selecione o idioma **Portuguese** em `Additional language data`. Se o idioma não tiver sido selecionado, coloque o arquivo `por.traineddata` na pasta `tessdata` da instalação.

Feche e abra o terminal após a instalação. No Windows, a configuração recomendada é preencher o arquivo `.env` do projeto desta forma:

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

Se o PowerShell informar que `tesseract` não é reconhecido, confirme primeiro a instalação usando o caminho completo:

```powershell
& "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
```

Para disponibilizar o comando em novos terminais, adicione `C:\Program Files\Tesseract-OCR` à variável de ambiente `Path` do usuário. Isso pode ser feito em **Configurações avançadas do sistema > Variáveis de Ambiente > Variáveis do usuário > Path**. Depois da alteração, feche e abra o PowerShell e execute novamente `tesseract --version`.

Confira também os idiomas instalados:

```powershell
& "C:\Program Files\Tesseract-OCR\tesseract.exe" --list-langs
```

Se `por` não aparecer, execute novamente o instalador como administrador, escolha a opção de modificar a instalação e selecione **Portuguese** em `Additional language data`. A instalação correta deve criar `C:\Program Files\Tesseract-OCR\tessdata\por.traineddata`.

Ou use o script abaixo em powershell para instalar o idioma português:

$tesseract = "C:\Program Files\Tesseract-OCR\tesseract.exe"
$tessdata  = Join-Path (Split-Path $tesseract) "tessdata"

if (-not (Test-Path $tesseract)) {
    throw "Tesseract não encontrado em $tesseract. Localize tesseract.exe e ajuste o caminho."
}

$destino = Join-Path $tessdata "por.traineddata"
Invoke-WebRequest `
    -Uri "https://github.com/tesseract-ocr/tessdata/raw/refs/heads/main/por.traineddata" `
    -OutFile $destino

& $tesseract --list-langs


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

A saída de `tesseract --list-langs` deve conter `por`. Em seguida, valide as dependências do projeto:

```bash
python .\src\pfcompara\validar_ambiente.py
```

O MVP aplica OCR do Tesseract a arquivos de imagem. PDFs que já possuem camada de texto são lidos diretamente; OCR de PDFs digitalizados é uma limitação conhecida desta versão.

## Ollama

```bash
ollama pull llama3.1:8b
ollama serve
```

Use `LLM_PROVIDER=ollama`.

## OpenAI

Defina `LLM_PROVIDER=openai`, `OPENAI_API_KEY` e `OPENAI_MODEL`. Não grave chaves em commits.

## Execução

## Aplicação para OCR: precisa estar em execução
API:

```powershell
$env:PYTHONPATH = "src"

python -m pfcompara.main
```

## Aplicação principal WEB
Interface:

```powershell
$env:PYTHONPATH = "src"

streamlit run src/pfcompara/ui/app.py
```

No Linux ou macOS, defina a variável com `export PYTHONPATH=src`. No Prompt de Comando clássico do Windows (`cmd.exe`), use `set PYTHONPATH=src`.

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

A documentação de apoio foi separada do código principal e está em `../PfCompara_Apoio/docs`. O relatório técnico final em DOCX pode ser regenerado com:

```powershell
python ..\PfCompara_Apoio\ferramentas\gerar_relatorio_tecnico.py
```

O arquivo é criado em `../PfCompara_Artefatos/Relatorio_Tecnico_PfCompara.docx` e começa com um diagrama de blocos da arquitetura, do fluxo operacional e dos objetos Python executados.

## Organização dos diretórios

- `PfCompara`: somente aplicação principal, configuração, persistência local e arquivos de implantação.
- `PfCompara_Apoio/docs`: documentação complementar e decisões arquiteturais.
- `PfCompara_Apoio/desenvolvimento/tests`: testes automatizados.
- `PfCompara_Apoio/ferramentas`: geração de artefatos, validação e manutenção.
- `PfCompara_Apoio/diagramas`: imagens intermediárias do relatório técnico.
- `PfCompara_Artefatos/Relatorio_Tecnico_PfCompara.docx`: relatório técnico com diagrama de objetos Python.
- `PfCompara_Artefatos/IA4Seg_PfCompara_Apresentacao.pptx`: apresentação funcional e técnica.
- `PfCompara_Artefatos/IA4Seg_PfCompara_Tutorial.mp4`: tutorial real de importação e comparação.
- `PfCompara_Artefatos/codigo_fonte_PfCompara.zip`: pacote do código-fonte sem segredos, banco local ou ambiente virtual.

## Testes

```powershell
python -m pytest ..\PfCompara_Apoio\desenvolvimento\tests
```

## Limitações conhecidas

OCR pode falhar em documentos de baixa qualidade. LLMs podem interpretar cláusulas ambíguas de forma equivocada. O MVP não substitui corretores, subscritores, advogados, reguladores ou especialistas em seguros.

## Responsável pelo produto

IA4Seg

## Licença

Distribuído sob licença MIT. Consulte `LICENSE`.
