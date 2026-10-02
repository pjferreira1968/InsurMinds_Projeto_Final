"""Schemas da API REST do InsurMinds_Projeto_Final."""

from __future__ import annotations

from pydantic import BaseModel, Field

from insurminds_projeto_final.dominio.enums import ModoComparacao


class RespostaDocumento(BaseModel):
    """Resposta pública de documento sem expor caminho interno completo."""

    id: int
    nome_original: str
    status: str
    mensagem: str


class RequisicaoComparacao(BaseModel):
    """Entrada para criação de comparação entre duas apólices."""

    apolice_a_id: int
    apolice_b_id: int
    modo: ModoComparacao = ModoComparacao.COMPLETA
    pontos_relevantes_ids: list[str] = Field(default_factory=list)
