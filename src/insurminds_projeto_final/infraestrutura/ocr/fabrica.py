"""Fábrica de provedores de OCR e extração textual."""

from __future__ import annotations

from pathlib import Path

from insurminds_projeto_final.configuracao.settings import Settings
from insurminds_projeto_final.dominio.modelos import ResultadoExtracao
from insurminds_projeto_final.infraestrutura.ocr.pdf_texto import ClientePDFTexto
from insurminds_projeto_final.infraestrutura.ocr.tesseract import ClienteTesseractOCR


class ClienteOCRAuto:
    """Seleciona extração textual de PDF ou OCR conforme o tipo do arquivo."""

    def __init__(self, settings: Settings) -> None:
        """Cria os clientes de texto nativo e Tesseract disponíveis."""

        self.pdf = ClientePDFTexto()
        self.tesseract = ClienteTesseractOCR(settings)

    def extrair(self, caminho: Path) -> ResultadoExtracao:
        """Executa a melhor estratégia disponível para o arquivo recebido."""

        if caminho.suffix.lower() == ".pdf":
            resultado = self.pdf.extrair(caminho)
            if resultado.texto.strip():
                return resultado
            resultado.observacoes.append("PDF sem texto nativo; enviar imagem ou configurar OCR de PDF.")
            return resultado
        return self.tesseract.extrair(caminho)


def criar_cliente_ocr(settings: Settings):
    """Cria o cliente de OCR configurado para o ambiente atual."""

    if settings.ocr_provider in {"auto", "tesseract"}:
        return ClienteOCRAuto(settings) if settings.ocr_provider == "auto" else ClienteTesseractOCR(settings)
    return ClienteOCRAuto(settings)
