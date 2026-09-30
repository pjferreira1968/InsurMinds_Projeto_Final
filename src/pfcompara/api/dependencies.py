"""Dependências compartilhadas da API FastAPI."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy.orm import Session

from pfcompara.agentes.comparacao import AgenteComparacao
from pfcompara.agentes.estruturacao import AgenteEstruturacao
from pfcompara.agentes.extracao_texto import AgenteExtracaoTexto
from pfcompara.agentes.identificacao_clausulas import AgenteIdentificacaoClausulas
from pfcompara.agentes.orquestrador import OrquestradorProcessamento
from pfcompara.agentes.persistencia import AgentePersistencia
from pfcompara.agentes.recepcao import AgenteRecepcao
from pfcompara.agentes.relatorio import AgenteRelatorio
from pfcompara.configuracao.settings import obter_settings
from pfcompara.infraestrutura.armazenamento.arquivos import ServicoArmazenamentoArquivos
from pfcompara.infraestrutura.banco.conexao import obter_sessao
from pfcompara.infraestrutura.banco.repositorios import RepositorioApolices
from pfcompara.infraestrutura.llm.fabrica import criar_cliente_llm
from pfcompara.infraestrutura.ocr.fabrica import criar_cliente_ocr
from pfcompara.servicos.comparacao_apolices import ServicoComparacaoApolices
from pfcompara.servicos.consulta_apolices import ServicoConsultaApolices
from pfcompara.servicos.geracao_relatorio import ServicoGeracaoRelatorio
from pfcompara.servicos.gestao_apolices import ServicoGestaoApolices
from pfcompara.servicos.ingestao_documento import ServicoIngestaoDocumento
from pfcompara.servicos.processamento_apolice import ServicoProcessamentoApolice


def obter_repositorio(sessao: Session) -> RepositorioApolices:
    """Cria repositório para a sessão atual."""

    return RepositorioApolices(sessao)


def dependencia_sessao() -> Iterator[Session]:
    """Encaminha sessão SQLAlchemy para o sistema de dependências FastAPI."""

    yield from obter_sessao()


def criar_servicos(sessao: Session):
    """Monta os serviços da aplicação para uma requisição."""

    settings = obter_settings()
    repositorio = obter_repositorio(sessao)
    armazenamento = ServicoArmazenamentoArquivos(settings)
    recepcao = AgenteRecepcao(armazenamento, repositorio)
    extracao = AgenteExtracaoTexto(criar_cliente_ocr(settings))
    identificacao = AgenteIdentificacaoClausulas(criar_cliente_llm(settings))
    estruturacao = AgenteEstruturacao()
    persistencia = AgentePersistencia(repositorio)
    orquestrador = OrquestradorProcessamento(repositorio, extracao, identificacao, estruturacao, persistencia)
    relatorio = AgenteRelatorio(Path(settings.storage_path) / "relatorios")
    return {
        "ingestao": ServicoIngestaoDocumento(recepcao),
        "processamento": ServicoProcessamentoApolice(repositorio, armazenamento, orquestrador),
        "consulta": ServicoConsultaApolices(repositorio),
        "gestao": ServicoGestaoApolices(repositorio, armazenamento),
        "comparacao": ServicoComparacaoApolices(repositorio, AgenteComparacao()),
        "relatorio": ServicoGeracaoRelatorio(repositorio, relatorio),
        "repositorio": repositorio,
    }
