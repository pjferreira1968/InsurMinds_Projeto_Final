"""Rotas de saúde operacional da API."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["saúde"])


@router.get("/saude")
def verificar_saude() -> dict[str, str]:
    """Retorna status básico da aplicação."""

    return {"status": "ok", "mensagem": "PfCompara está operacional."}
