"""Agente de estruturação e validação dos dados de apólice."""

from __future__ import annotations

from insurminds_projeto_final.dominio.modelos import ApoliceEstruturada
from insurminds_projeto_final.dominio.schemas_extracao import RespostaLLMExtracao
from insurminds_projeto_final.excecoes import ErroValidacaoEstruturacao


class AgenteEstruturacao:
    """Converte a resposta validada da LLM em modelo de domínio persistível."""

    def estruturar(self, resposta: RespostaLLMExtracao) -> ApoliceEstruturada:
        """Valida suficiência mínima para registrar uma apólice."""

        apolice = resposta.apolice
        if not any([apolice.numero, apolice.seguradora, apolice.segurado, apolice.limites, apolice.coberturas]):
            raise ErroValidacaoEstruturacao("Não foram identificados dados mínimos de apólice.")
        return apolice
