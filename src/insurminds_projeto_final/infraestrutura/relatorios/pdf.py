"""Relatório PDF de comparação orientado ao público de seguros D&O."""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from insurminds_projeto_final.configuracao.constantes import AVISO_REVISAO_HUMANA, EMPRESA_PRODUTO, NOME_PRODUTO
from insurminds_projeto_final.dominio.enums import ClassificacaoComparacao
from insurminds_projeto_final.dominio.schemas_comparacao import ItemComparacao, ResultadoComparacao


ROTULOS_CLASSIFICACAO = {
    ClassificacaoComparacao.EQUIVALENTE: "Equivalente",
    ClassificacaoComparacao.DIFERENTE: "Diferente",
    ClassificacaoComparacao.AUSENTE_A: "Ausente na A",
    ClassificacaoComparacao.AUSENTE_B: "Ausente na B",
    ClassificacaoComparacao.INDETERMINADO: "Não identificado",
    ClassificacaoComparacao.NAO_ENCONTRADO: "Não encontrado",
}


class GeradorRelatorioPDF:
    """Renderiza um relatório executivo e comparativo em Português do Brasil."""

    def gerar(self, resultado: ResultadoComparacao, caminho: Path) -> Path:
        """Cria o PDF com identificação clara, resumo e pontos de atenção."""

        caminho.parent.mkdir(parents=True, exist_ok=True)
        estilos = self._estilos()
        documento = SimpleDocTemplate(
            str(caminho),
            pagesize=A4,
            rightMargin=16 * mm,
            leftMargin=16 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title=f"{NOME_PRODUTO} | Relatório de comparação de apólices D&O",
            author=EMPRESA_PRODUTO,
        )

        divergentes = [
            item
            for item in resultado.itens
            if item.classificacao != ClassificacaoComparacao.EQUIVALENTE
        ]
        equivalentes = len(resultado.itens) - len(divergentes)
        elementos = [
            Paragraph(f"{EMPRESA_PRODUTO} | {NOME_PRODUTO}", estilos["Marca"]),
            Paragraph("Relatório de comparação de apólices D&amp;O", estilos["Titulo"]),
            Paragraph(
                f"Modo {resultado.modo.value.capitalize()} | Apoio à análise técnica e comercial",
                estilos["Subtitulo"],
            ),
            Paragraph(
                "Pontos relevantes selecionados: "
                + escape("; ".join(resultado.pontos_relevantes_selecionados)),
                estilos["Subtitulo"],
            ) if resultado.pontos_relevantes_selecionados else Spacer(1, 0),
            Spacer(1, 7 * mm),
            self._tabela_apolices(resultado, estilos),
            Spacer(1, 6 * mm),
            Paragraph("Resumo executivo", estilos["Heading1"]),
            Paragraph(escape(resultado.resumo), estilos["Corpo"]),
            Spacer(1, 3 * mm),
            self._tabela_metricas(len(resultado.itens), len(divergentes), equivalentes, estilos),
            Spacer(1, 6 * mm),
            Paragraph("Parecer ponderado", estilos["Heading1"]),
            Paragraph(escape(resultado.parecer), estilos["Corpo"]),
            Paragraph(
                f"Pontuação da Apólice A: <b>{resultado.pontuacao_apolice_a:g}</b> &nbsp;&nbsp; "
                f"Pontuação da Apólice B: <b>{resultado.pontuacao_apolice_b:g}</b>",
                estilos["Corpo"],
            ),
            Spacer(1, 6 * mm),
            Spacer(1, 6 * mm),
            Paragraph(escape(AVISO_REVISAO_HUMANA), estilos["Aviso"]),
            Spacer(1, 6 * mm),
            Paragraph("Quadro comparativo", estilos["Heading1"]),
            Paragraph(
                "As divergências e ausências estão destacadas nas próprias linhas. Campos não identificados devem ser conferidos diretamente nas condições contratuais.",
                estilos["Corpo"],
            ),
            Spacer(1, 3 * mm),
            self._tabela_legenda(estilos),
            Spacer(1, 4 * mm),
            self._tabela_itens(resultado.itens, estilos),
        ]
        documento.build(elementos, onFirstPage=self._rodape, onLaterPages=self._rodape)
        return caminho

    @staticmethod
    def _estilos() -> dict[str, ParagraphStyle]:
        """Define a identidade visual e a tipografia do relatório."""

        base = getSampleStyleSheet()
        return {
            "Marca": ParagraphStyle(
                "Marca",
                parent=base["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=10,
                textColor=colors.HexColor("#0F766E"),
                spaceAfter=3,
            ),
            "Titulo": ParagraphStyle(
                "Titulo",
                parent=base["Title"],
                fontName="Helvetica-Bold",
                fontSize=19,
                leading=23,
                textColor=colors.HexColor("#17324D"),
                alignment=TA_LEFT,
                spaceAfter=5,
            ),
            "Subtitulo": ParagraphStyle(
                "Subtitulo",
                parent=base["BodyText"],
                fontSize=10,
                textColor=colors.HexColor("#52606D"),
            ),
            "Heading1": ParagraphStyle(
                "TituloSecao",
                parent=base["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=13,
                leading=16,
                textColor=colors.HexColor("#17324D"),
                spaceBefore=3,
                spaceAfter=6,
            ),
            "Corpo": ParagraphStyle(
                "Corpo",
                parent=base["BodyText"],
                fontSize=9,
                leading=13,
                textColor=colors.HexColor("#273444"),
            ),
            "Lista": ParagraphStyle(
                "Lista",
                parent=base["BodyText"],
                fontSize=8.5,
                leading=12,
                leftIndent=4 * mm,
                firstLineIndent=-3 * mm,
                bulletIndent=0,
                spaceAfter=3,
            ),
            "Aviso": ParagraphStyle(
                "Aviso",
                parent=base["BodyText"],
                fontSize=8,
                leading=11,
                textColor=colors.HexColor("#7A2E0E"),
                backColor=colors.HexColor("#FFF4E5"),
                borderPadding=7,
            ),
            "Celula": ParagraphStyle(
                "Celula",
                parent=base["BodyText"],
                fontSize=7.2,
                leading=9.2,
                textColor=colors.HexColor("#273444"),
            ),
            "CelulaCentro": ParagraphStyle(
                "CelulaCentro",
                parent=base["BodyText"],
                fontSize=7.2,
                leading=9.2,
                alignment=TA_CENTER,
            ),
            "CelulaCabecalho": ParagraphStyle(
                "CelulaCabecalho",
                parent=base["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=7.2,
                leading=9.2,
                alignment=TA_CENTER,
                textColor=colors.white,
            ),
        }

    @staticmethod
    def _tabela_apolices(resultado: ResultadoComparacao, estilos) -> Table:
        """Monta o cabeçalho que identifica as apólices comparadas."""

        dados = [
            [
                Paragraph("APÓLICE A", estilos["CelulaCabecalho"]),
                Paragraph("APÓLICE B", estilos["CelulaCabecalho"]),
            ],
            [Paragraph(escape(resultado.apolice_a_nome), estilos["Corpo"]), Paragraph(escape(resultado.apolice_b_nome), estilos["Corpo"])],
        ]
        tabela = Table(dados, colWidths=[88 * mm, 88 * mm])
        tabela.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324D")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#B8C4CE")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9E0E6")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        return tabela

    @staticmethod
    def _tabela_metricas(total: int, divergentes: int, equivalentes: int, estilos) -> Table:
        """Resume as quantidades de critérios, divergências e equivalências."""

        dados = [
            [
                Paragraph(f"<b>{total}</b><br/>Critérios analisados", estilos["CelulaCentro"]),
                Paragraph(f"<b>{divergentes}</b><br/>Divergências", estilos["CelulaCentro"]),
                Paragraph(f"<b>{equivalentes}</b><br/>Itens equivalentes", estilos["CelulaCentro"]),
            ]
        ]
        tabela = Table(dados, colWidths=[58.6 * mm] * 3)
        tabela.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF3F7")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#B8C4CE")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9E0E6")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ]
            )
        )
        return tabela

    @staticmethod
    def _tabela_legenda(estilos) -> Table:
        """Explica as cores utilizadas nas linhas do quadro comparativo."""

        itens = [
            ("Equivalente", colors.HexColor("#CFE8FF")),
            ("Diferente", colors.HexColor("#FFE08A")),
            ("Ausente em uma apólice", colors.HexColor("#F7B7C3")),
            ("Não identificado", colors.HexColor("#D7DCE2")),
            ("Não encontrado", colors.HexColor("#E2C6F2")),
        ]
        dados = [[Paragraph(rotulo, estilos["CelulaCentro"]) for rotulo, _ in itens]]
        tabela = Table(dados, colWidths=[35.2 * mm] * 5)
        estilo = [
            ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#B8C4CE")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CED7DE")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
        for coluna, (_, fundo) in enumerate(itens):
            estilo.append(("BACKGROUND", (coluna, 0), (coluna, 0), fundo))
        tabela.setStyle(TableStyle(estilo))
        return tabela

    def _tabela_itens(self, itens: list[ItemComparacao], estilos) -> Table:
        """Renderiza os itens comparados e destaca sua classificação."""

        cabecalho = ["Critério", "Apólice A", "Apólice B", "Peso", "Conclusão"]
        dados = [[Paragraph(titulo, estilos["CelulaCabecalho"]) for titulo in cabecalho]]
        for item in itens:
            conclusao = f"{ROTULOS_CLASSIFICACAO[item.classificacao]}<br/>{escape(item.impacto)}"
            ponto_relevante = item.criterio_relevante or item.campo
            detalhe = f"<br/>{escape(item.campo)}" if ponto_relevante != item.campo else ""
            dados.append(
                [
                    Paragraph(
                        f"<b>{escape(ponto_relevante)}</b>{detalhe}<br/>{escape(item.categoria)}",
                        estilos["Celula"],
                    ),
                    Paragraph(escape(item.valor_apolice_a or "Não identificado"), estilos["Celula"]),
                    Paragraph(escape(item.valor_apolice_b or "Não identificado"), estilos["Celula"]),
                    Paragraph(f"{item.peso:g}" if item.peso else "-", estilos["CelulaCentro"]),
                    Paragraph(conclusao, estilos["Celula"]),
                ]
            )
        tabela = Table(dados, repeatRows=1, colWidths=[34 * mm, 48 * mm, 48 * mm, 12 * mm, 34 * mm])
        estilo = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324D")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CED7DE")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
        for indice, item in enumerate(itens, start=1):
            if item.classificacao == ClassificacaoComparacao.EQUIVALENTE:
                fundo = colors.HexColor("#CFE8FF")
            elif item.classificacao == ClassificacaoComparacao.INDETERMINADO:
                fundo = colors.HexColor("#D7DCE2")
            elif item.classificacao == ClassificacaoComparacao.NAO_ENCONTRADO:
                fundo = colors.HexColor("#E2C6F2")
            elif item.classificacao in (
                ClassificacaoComparacao.AUSENTE_A,
                ClassificacaoComparacao.AUSENTE_B,
            ):
                fundo = colors.HexColor("#F7B7C3")
            else:
                fundo = colors.HexColor("#FFE08A")
            estilo.append(("BACKGROUND", (0, indice), (-1, indice), fundo))
        tabela.setStyle(TableStyle(estilo))
        return tabela

    @staticmethod
    def _rodape(canvas, documento) -> None:
        """Inclui empresa, produto e número da página no rodapé."""

        canvas.saveState()
        largura, _ = A4
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#667085"))
        canvas.drawString(
            16 * mm,
            10 * mm,
            f"{EMPRESA_PRODUTO} | {NOME_PRODUTO} | Relatório de apoio à análise D&O",
        )
        canvas.drawRightString(largura - 16 * mm, 10 * mm, f"Página {documento.page}")
        canvas.restoreState()
