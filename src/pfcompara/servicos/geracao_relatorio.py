"""Serviço de geração de relatórios para comparações persistidas."""

from __future__ import annotations

from pathlib import Path

from pfcompara.agentes.relatorio import AgenteRelatorio
from pfcompara.dominio.schemas_comparacao import ResultadoComparacao
from pfcompara.infraestrutura.banco.repositorios import RepositorioApolices


class ServicoGeracaoRelatorio:
    """Gera relatórios HTML e PDF a partir de uma comparação salva."""

    def __init__(self, repositorio: RepositorioApolices, agente: AgenteRelatorio) -> None:
        """Recebe os componentes de consulta e geração de relatórios."""

        self.repositorio = repositorio
        self.agente = agente

    def gerar(self, comparacao_id: int) -> tuple[Path, Path]:
        """Gera arquivos de relatório e retorna seus caminhos locais."""

        comparacao = self.repositorio.obter_comparacao(comparacao_id)
        if comparacao is None:
            raise ValueError("Comparação não encontrada.")
        resultado = ResultadoComparacao.model_validate(comparacao.resultado)
        return self.agente.gerar(comparacao.id, resultado)
