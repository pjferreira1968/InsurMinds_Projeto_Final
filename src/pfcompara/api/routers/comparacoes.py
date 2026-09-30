"""Rotas de criação e consulta de comparações."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from pfcompara.api.dependencies import criar_servicos, dependencia_sessao
from pfcompara.api.schemas import RequisicaoComparacao

router = APIRouter(prefix="/api/v1/comparacoes", tags=["comparações"])


@router.post("")
def criar_comparacao(requisicao: RequisicaoComparacao, sessao: Session = Depends(dependencia_sessao)) -> dict[str, object]:
    """Cria comparação entre duas apólices."""

    try:
        comparacao = criar_servicos(sessao)["comparacao"].comparar(
            requisicao.apolice_a_id,
            requisicao.apolice_b_id,
            requisicao.modo,
            pontos_relevantes_ids=requisicao.pontos_relevantes_ids,
        )
        return {"id": comparacao.id, "resultado": comparacao.resultado}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{comparacao_id}")
def obter_comparacao(comparacao_id: int, sessao: Session = Depends(dependencia_sessao)) -> dict[str, object]:
    """Consulta comparação persistida."""

    comparacao = criar_servicos(sessao)["repositorio"].obter_comparacao(comparacao_id)
    if comparacao is None:
        raise HTTPException(status_code=404, detail="Comparação não encontrada.")
    return {"id": comparacao.id, "resultado": comparacao.resultado}
