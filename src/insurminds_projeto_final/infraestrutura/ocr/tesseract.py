"""OCR local usando Tesseract quando disponível no ambiente."""

from __future__ import annotations

from pathlib import Path

import pytesseract
from PIL import Image

from insurminds_projeto_final.configuracao.settings import Settings
from insurminds_projeto_final.dominio.modelos import ResultadoExtracao
from insurminds_projeto_final.excecoes import ErroOCR


class ClienteTesseractOCR:
    """Executa OCR em imagens suportadas pelo Pillow e Tesseract."""

    def __init__(self, settings: Settings) -> None:
        """Configura o executável Tesseract indicado no ambiente."""

        self.settings = settings
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    def extrair(self, caminho: Path) -> ResultadoExtracao:
        """Extrai texto por OCR de uma imagem.

        PDFs digitalizados exigem `pdf2image` em evolução futura; no MVP, PDFs
        sem camada textual são sinalizados para revisão quando o OCR direto não
        puder processá-los.
        """

        try:
            with Image.open(caminho) as imagem:
                texto = pytesseract.image_to_string(imagem, lang=self.settings.ocr_language)
        except Exception as exc:
            raise ErroOCR(f"O OCR local não conseguiu processar o arquivo: {exc}") from exc
        return ResultadoExtracao(texto=texto.strip(), metodo="ocr_tesseract", paginas=1)
