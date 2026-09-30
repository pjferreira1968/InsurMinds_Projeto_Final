"""Agente de identificação de cláusulas por IA Generativa."""

from __future__ import annotations

import logging

from pfcompara.dominio.schemas_extracao import RespostaLLMExtracao
from pfcompara.infraestrutura.llm.heuristico import ClienteHeuristicoDemo


logger = logging.getLogger(__name__)


class AgenteIdentificacaoClausulas:
    """Solicita a um provedor LLM a identificação de cláusulas relevantes."""

    def __init__(self, cliente_llm) -> None:
        """Recebe o provedor de IA usado na identificação de cláusulas."""

        self.cliente_llm = cliente_llm

    def identificar(self, texto: str, registrar=None) -> RespostaLLMExtracao:
        """Executa extração por LLM e usa heurística local quando necessário."""

        try:
            resposta = self.cliente_llm.extrair_apolice(texto)
            apolice = resposta.apolice
            if any(
                [
                    apolice.numero,
                    apolice.seguradora,
                    apolice.segurado,
                    apolice.limites,
                    apolice.coberturas,
                ]
            ):
                return resposta
            raise ValueError("O provedor não identificou campos mínimos.")
        except Exception as exc:
            logger.warning("Extração por LLM indisponível ou inválida: %s", exc)
            if registrar:
                registrar(
                    "[AgenteIdentificacaoClausulas.identificar] A resposta do provedor não passou "
                    "na validação; aplicando ClienteHeuristicoDemo.extrair_apolice como contingência."
                )
            return ClienteHeuristicoDemo().extrair_apolice(texto)
