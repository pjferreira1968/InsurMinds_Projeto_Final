"""Extração de texto nativo de PDFs por `pypdf`."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from pfcompara.dominio.modelos import ResultadoExtracao


class ClientePDFTexto:
    """Extrai texto embutido de PDFs textuais antes de recorrer a OCR."""

    def extrair(self, caminho: Path) -> ResultadoExtracao:
        """Retorna texto de páginas PDF quando há camada textual disponível."""

        leitor = PdfReader(str(caminho))
        textos = [(pagina.extract_text() or "") for pagina in leitor.pages]
        texto = "\n\n".join(t.strip() for t in textos if t.strip())
        metodo = "pdf_textual" if texto.strip() else "vazio"
        return ResultadoExtracao(texto=texto, metodo=metodo, paginas=max(len(leitor.pages), 1))
