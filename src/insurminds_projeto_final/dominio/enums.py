"""Enums de domínio usados nos fluxos de documento, apólice e comparação."""

from __future__ import annotations

from enum import StrEnum


class StatusDocumento(StrEnum):
    """Estados possíveis de um documento recebido pela plataforma."""

    RECEBIDO = "recebido"
    PROCESSANDO = "processando"
    PROCESSADO = "processado"
    FALHA = "falha"


class ClassificacaoComparacao(StrEnum):
    """Classificação de diferenças entre itens de duas apólices."""

    EQUIVALENTE = "equivalente"
    DIFERENTE = "diferente"
    AUSENTE_A = "ausente_na_apolice_a"
    AUSENTE_B = "ausente_na_apolice_b"
    INDETERMINADO = "indeterminado"
    NAO_ENCONTRADO = "nao_encontrado"


class ModoComparacao(StrEnum):
    """Níveis de detalhamento disponíveis para a comparação."""

    COMPLETA = "completa"
    RELEVANTE = "relevante"
