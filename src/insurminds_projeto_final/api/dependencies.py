"""Dependências compartilhadas da API FastAPI."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy.orm import Session

from insurminds_projeto_final.agentes.comparacao import AgenteComparacao
from insurminds_projeto_final.agentes.estruturacao import AgenteEstruturacao
from insurminds_projeto_final.agentes.extracao_texto import AgenteExtracaoTexto
from insurminds_projeto_final.agentes.identificacao_clausulas import AgenteIdentificacaoClausulas
from insurminds_projeto_final.agentes.orquestrador import OrquestradorProcessamento
from insurminds_projeto_final.agentes.persistencia import AgentePersistencia
from insurminds_projeto_final.agentes.recepcao import AgenteRecepcao
from insurminds_projeto_final.agentes.relatorio import AgenteRelatorio
from insurminds_projeto_final.configuracao.settings import obter_settings
from insurminds_projeto_final.infraestrutura.armazenamento.arquivos import ServicoArmazenamentoArquivos
from insurminds_projeto_final.infraestrutura.banco.conexao import obter_sessao
from insurminds_projeto_final.infraestrutura.banco.repositorios import RepositorioApolices
from insurminds_projeto_final.infraestrutura.llm.fabrica import criar_cliente_llm
from insurminds_projeto_final.infraestrutura.ocr.fabrica import criar_cliente_ocr
from insurminds_projeto_final.servicos.comparacao_apolices import ServicoComparacaoApolices
from insurminds_projeto_final.servicos.consulta_apolices import ServicoConsultaApolices
from insurminds_projeto_final.servicos.geracao_relatorio import ServicoGeracaoRelatorio
from insurminds_projeto_final.servicos.gestao_apolices import ServicoGestaoApolices
from insurminds_projeto_final.servicos.ingestao_documento import ServicoIngestaoDocumento
from insurminds_projeto_final.servicos.processamento_apolice import ServicoProcessamentoApolice


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
