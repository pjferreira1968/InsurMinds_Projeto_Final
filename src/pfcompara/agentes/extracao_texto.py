"""Agente de extração textual e OCR para documentos recebidos."""

from __future__ import annotations

from pathlib import Path

from pfcompara.dominio.modelos import ResultadoExtracao


class AgenteExtracaoTexto:
    """Coordena extração de texto nativo ou OCR a partir de um cliente configurado."""

    def __init__(self, cliente_ocr) -> None:
        """Recebe o cliente responsável por texto nativo e OCR."""

        self.cliente_ocr = cliente_ocr

    def extrair(self, caminho: Path) -> ResultadoExtracao:
        """Extrai texto e preserva observações relevantes para auditoria."""

        return self.cliente_ocr.extrair(caminho)
