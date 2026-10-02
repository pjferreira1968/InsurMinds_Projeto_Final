"""Agente de identificação de cláusulas por IA Generativa."""

from __future__ import annotations

import logging

from insurminds_projeto_final.dominio.modelos import ApoliceEstruturada
from insurminds_projeto_final.dominio.schemas_extracao import RespostaLLMExtracao
from insurminds_projeto_final.infraestrutura.llm.heuristico import ClienteHeuristicoDemo


logger = logging.getLogger(__name__)


class AgenteIdentificacaoClausulas:
    """Solicita a um provedor LLM a identificação de cláusulas relevantes."""

    def __init__(self, cliente_llm) -> None:
        """Recebe o provedor de IA usado na identificação de cláusulas."""

        self.cliente_llm = cliente_llm

    def identificar(self, texto: str, registrar=None) -> RespostaLLMExtracao:
        """Executa a LLM e complementa campos explícitos por regras determinísticas."""

        resposta_local = ClienteHeuristicoDemo().extrair_apolice(texto)
        try:
            resposta = self.cliente_llm.extrair_apolice(texto)
            resposta.apolice, complementada = self._combinar_apolices(
                resposta.apolice,
                resposta_local.apolice,
            )
            if complementada:
                resposta.requer_revisao_humana = True
                resposta.justificativa = (
                    f"{resposta.justificativa} Campos explícitos foram validados e "
                    "complementados por evidências textuais determinísticas."
                ).strip()
                if registrar:
                    registrar(
                        "[AgenteIdentificacaoClausulas._combinar_apolices] "
                        "Validando e complementando campos explícitos da resposta LLM."
                    )
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
                    "[AgenteIdentificacaoClausulas.identificar] O provedor LLM "
                    "falhou ou não passou "
                    f"na validação ({exc}); aplicando "
                    "ClienteHeuristicoDemo.extrair_apolice como contingência."
                )
            return resposta_local

    @classmethod
    def _combinar_apolices(
        cls,
        principal: ApoliceEstruturada,
        complementar: ApoliceEstruturada,
    ) -> tuple[ApoliceEstruturada, bool]:
        """Mescla a LLM com campos objetivos e evidências extraídos do texto."""

        combinada = principal.model_copy(deep=True)
        alterada = False
        for campo in (
            "numero",
            "seguradora",
            "segurado",
            "inicio_vigencia",
            "fim_vigencia",
        ):
            valor = getattr(complementar, campo)
            if valor is not None and valor != getattr(combinada, campo):
                setattr(combinada, campo, valor)
                alterada = True

        for campo in ("limites", "franquias", "coberturas", "exclusoes", "clausulas"):
            atuais = list(getattr(combinada, campo))
            mesclados = cls._mesclar_itens(atuais, list(getattr(complementar, campo)))
            if mesclados != atuais:
                setattr(combinada, campo, mesclados)
                alterada = True

        if not combinada.aviso and complementar.aviso:
            combinada.aviso = complementar.aviso
            alterada = True
        return combinada, alterada

    @staticmethod
    def _mesclar_itens(atuais: list, complementares: list) -> list:
        """Acrescenta itens determinísticos sem repetir estruturas idênticas."""

        resultado = list(atuais)
        assinaturas = {item.model_dump_json() for item in resultado}
        for item in complementares:
            assinatura = item.model_dump_json()
            if assinatura not in assinaturas:
                resultado.append(item)
                assinaturas.add(assinatura)
        return resultado
