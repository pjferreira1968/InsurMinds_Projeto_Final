"""Schemas validados para respostas de extração por LLM.

O contrato prioriza campos essenciais do MVP e evidencia as informações que
precisam de revisão humana quando a LLM ou as regras não alcançam confiança
suficiente.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from pfcompara.dominio.modelos import ApoliceEstruturada


class RespostaLLMExtracao(BaseModel):
    """Resposta estruturada esperada dos provedores de IA Generativa."""

    apolice: ApoliceEstruturada
    confianca: float = Field(default=0.5, ge=0, le=1)
    requer_revisao_humana: bool = True
    justificativa: str = "Extração sujeita a revisão humana especializada."
