"""Schemas de comparação entre apólices D&O."""

from __future__ import annotations

from pydantic import BaseModel, Field

from insurminds_projeto_final.dominio.enums import ClassificacaoComparacao, ModoComparacao
from insurminds_projeto_final.dominio.modelos import Evidencia


class ItemComparacao(BaseModel):
    """Item individual de comparação com evidências e classificação."""

    categoria: str
    campo: str
    valor_apolice_a: str | None = None
    valor_apolice_b: str | None = None
    classificacao: ClassificacaoComparacao
    impacto: str
    evidencia_a: Evidencia | None = None
    evidencia_b: Evidencia | None = None
    criterio_relevante: str | None = None
    peso: float = 0
    pontos_apolice_a: float = 0
    pontos_apolice_b: float = 0


class ResultadoComparacao(BaseModel):
    """Resultado consolidado de comparação entre duas apólices."""

    apolice_a_id: int
    apolice_b_id: int
    apolice_a_nome: str = "Apólice A"
    apolice_b_nome: str = "Apólice B"
    modo: ModoComparacao = ModoComparacao.COMPLETA
    pontos_relevantes_selecionados: list[str] = Field(default_factory=list)
    itens: list[ItemComparacao] = Field(default_factory=list)
    resumo: str
    pontos_atencao: list[str] = Field(default_factory=list)
    pontuacao_apolice_a: float = 0
    pontuacao_apolice_b: float = 0
    parecer: str = "Parecer não calculado."
