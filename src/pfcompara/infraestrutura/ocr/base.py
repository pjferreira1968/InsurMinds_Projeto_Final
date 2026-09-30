"""Contratos de OCR e extração textual para documentos de apólices."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pfcompara.dominio.modelos import ResultadoExtracao


class ClienteOCRBase(Protocol):
    """Contrato implementado por provedores de extração textual e OCR.

    Implementações recebem um caminho local controlado pela aplicação e retornam
    texto, método usado e observações. Falhas recuperáveis devem lançar exceções
    específicas para que o orquestrador registre status claro ao usuário.
    """

    def extrair(self, caminho: Path) -> ResultadoExtracao:
        """Extrai texto de um documento local."""
