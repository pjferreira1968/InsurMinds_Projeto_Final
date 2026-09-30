"""Funções de pré-processamento de imagens para OCR.

O MVP mantém este módulo pequeno para evitar alterar evidências originais. Em
evoluções futuras, rotinas de deskew, binarização e redução de ruído devem
salvar cópias temporárias rastreáveis.
"""

from __future__ import annotations

from pathlib import Path


def manter_arquivo_original(caminho: Path) -> Path:
    """Retorna o próprio arquivo, preservando a evidência original no MVP."""

    return caminho
