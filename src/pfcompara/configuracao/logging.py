"""Configuração de logs estruturados em Português do Brasil.

Os logs usam formato JSON simples para facilitar busca por documento, agente,
status e duração. O módulo evita registrar conteúdo integral de documentos,
prompts ou segredos de ambiente.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    """Formata registros de log como JSON pesquisável."""

    def format(self, record: logging.LogRecord) -> str:
        """Converte um registro de log em JSON com campos de rastreabilidade."""

        dados: dict[str, Any] = {
            "data_hora": datetime.now(timezone.utc).isoformat(),
            "nivel": record.levelname,
            "mensagem": record.getMessage(),
            "modulo": record.name,
        }
        for campo in ("documento_id", "apolice_id", "agente", "status", "duracao_ms"):
            if hasattr(record, campo):
                dados[campo] = getattr(record, campo)
        return json.dumps(dados, ensure_ascii=False)


def configurar_logging(nivel: str = "INFO") -> None:
    """Configura o logger raiz com mensagens funcionais em pt-BR."""

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=nivel.upper(), handlers=[handler], force=True)
