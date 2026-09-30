"""Contratos de LLM para estruturação de apólices D&O."""

from __future__ import annotations

from typing import Protocol

from pfcompara.dominio.schemas_extracao import RespostaLLMExtracao


class ClienteLLMBase(Protocol):
    """Contrato para provedores de IA Generativa.

    Quem utiliza este contrato são os agentes de identificação e estruturação.
    Implementações devem receber texto extraído, solicitar uma resposta JSON ao
    provedor real e validar o retorno com Pydantic. Exceções de rede, timeout ou
    schema inválido devem ser transformadas em erros funcionais.
    """

    def extrair_apolice(self, texto: str) -> RespostaLLMExtracao:
        """Extrai dados estruturados de uma apólice a partir de texto bruto."""
