"""Rotas de download e visualização de relatórios."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from pfcompara.api.dependencies import criar_servicos, dependencia_sessao

router = APIRouter(prefix="/api/v1/comparacoes", tags=["relatórios"])


@router.get("/{comparacao_id}/relatorio.pdf")
def baixar_pdf(comparacao_id: int, sessao: Session = Depends(dependencia_sessao)) -> FileResponse:
    """Gera e retorna relatório PDF."""

    try:
        _, pdf = criar_servicos(sessao)["relatorio"].gerar(comparacao_id)
        return FileResponse(pdf, media_type="application/pdf", filename=pdf.name)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{comparacao_id}/relatorio.html")
def visualizar_html(comparacao_id: int, sessao: Session = Depends(dependencia_sessao)) -> FileResponse:
    """Gera e retorna relatório HTML."""

    try:
        html, _ = criar_servicos(sessao)["relatorio"].gerar(comparacao_id)
        return FileResponse(html, media_type="text/html", filename=html.name)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
