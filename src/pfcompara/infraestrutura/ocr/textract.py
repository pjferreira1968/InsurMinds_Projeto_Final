"""Placeholder explícito para futuro provedor Textract.

O MVP não aciona AWS Textract automaticamente porque a especificação não fornece
credenciais nem autorização. A classe documenta a evolução sem simular chamada
externa.
"""

from __future__ import annotations

from pathlib import Path

from pfcompara.dominio.modelos import ResultadoExtracao
from pfcompara.excecoes import ErroOCR


class ClienteTextractOCR:
    """Provê o contrato futuro para AWS Textract sem execução simulada."""

    def extrair(self, caminho: Path) -> ResultadoExtracao:
        """Interrompe o uso porque o provedor não está configurado no MVP."""

        raise ErroOCR("AWS Textract não está configurado neste MVP local.")
