"""Rotas de consulta de apólices processadas."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from pfcompara.api.dependencies import criar_servicos, dependencia_sessao

router = APIRouter(prefix="/api/v1/apolices", tags=["apólices"])


@router.get("")
def listar_apolices(sessao: Session = Depends(dependencia_sessao)) -> list[dict[str, object]]:
    """Lista apólices disponíveis para comparação."""

    return [
        {"id": a.id, "numero": a.numero, "seguradora": a.seguradora, "segurado": a.segurado}
        for a in criar_servicos(sessao)["consulta"].listar()
    ]


@router.get("/{apolice_id}")
def obter_apolice(apolice_id: int, sessao: Session = Depends(dependencia_sessao)) -> dict[str, object]:
    """Retorna dados estruturados de uma apólice."""

    apolice = criar_servicos(sessao)["consulta"].obter(apolice_id)
    if apolice is None:
        raise HTTPException(status_code=404, detail="Apólice não encontrada.")
    return {"id": apolice.id, "documento_id": apolice.documento_id, "dados": apolice.dados_estruturados}


@router.delete("/{apolice_id}")
def excluir_apolice(apolice_id: int, sessao: Session = Depends(dependencia_sessao)) -> dict[str, str]:
    """Exclui uma apólice e todos os dados derivados do documento."""

    try:
        criar_servicos(sessao)["gestao"].excluir(apolice_id)
        return {"mensagem": "Apólice e dados relacionados excluídos com sucesso."}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
