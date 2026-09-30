"""Rotas de upload e processamento de documentos."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from pfcompara.api.dependencies import criar_servicos, dependencia_sessao
from pfcompara.api.schemas import RespostaDocumento
from pfcompara.excecoes import ErroPfCompara

router = APIRouter(prefix="/api/v1/documentos", tags=["documentos"])


@router.post("", response_model=RespostaDocumento)
async def enviar_documento(arquivo: UploadFile = File(...), sessao: Session = Depends(dependencia_sessao)) -> RespostaDocumento:
    """Recebe documento enviado pelo usuário e registra status inicial."""

    servicos = criar_servicos(sessao)
    try:
        documento = servicos["ingestao"].enviar(arquivo.filename or "documento", await arquivo.read(), arquivo.content_type)
        return RespostaDocumento(id=documento.id, nome_original=documento.nome_original, status=documento.status, mensagem=documento.mensagem)
    except ErroPfCompara as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{documento_id}", response_model=RespostaDocumento)
def consultar_documento(documento_id: int, sessao: Session = Depends(dependencia_sessao)) -> RespostaDocumento:
    """Consulta status de documento por identificador."""

    repositorio = criar_servicos(sessao)["repositorio"]
    documento = repositorio.obter_documento(documento_id)
    if documento is None:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    return RespostaDocumento(id=documento.id, nome_original=documento.nome_original, status=documento.status, mensagem=documento.mensagem)


@router.post("/{documento_id}/processar")
def processar_documento(documento_id: int, sessao: Session = Depends(dependencia_sessao)) -> dict[str, object]:
    """Inicia processamento síncrono de documento."""

    try:
        apolice = criar_servicos(sessao)["processamento"].processar(documento_id)
        return {"mensagem": "Documento processado com sucesso.", "apolice_id": apolice.id}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
