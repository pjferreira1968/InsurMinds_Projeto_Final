"""Agente de geração de relatórios HTML e PDF."""

from __future__ import annotations

from pathlib import Path

from pfcompara.dominio.schemas_comparacao import ResultadoComparacao
from pfcompara.infraestrutura.relatorios.html import GeradorRelatorioHTML
from pfcompara.infraestrutura.relatorios.pdf import GeradorRelatorioPDF


class AgenteRelatorio:
    """Coordena a geração de relatórios exportáveis de comparação."""

    def __init__(self, diretorio: Path) -> None:
        """Configura o diretório e os geradores HTML e PDF."""

        self.diretorio = diretorio
        self.html = GeradorRelatorioHTML()
        self.pdf = GeradorRelatorioPDF()

    def gerar(self, comparacao_id: int, resultado: ResultadoComparacao) -> tuple[Path, Path]:
        """Gera relatório HTML e PDF para uma comparação persistida."""

        html = self.html.gerar(resultado, self.diretorio / f"comparacao_{comparacao_id}.html")
        pdf = self.pdf.gerar(resultado, self.diretorio / f"comparacao_{comparacao_id}.pdf")
        return html, pdf
