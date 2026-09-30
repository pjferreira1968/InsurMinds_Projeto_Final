"""Cliente real para Ollama local."""

from __future__ import annotations

import json

import httpx
from pydantic import ValidationError

from pfcompara.configuracao.settings import Settings
from pfcompara.dominio.schemas_extracao import RespostaLLMExtracao
from pfcompara.excecoes import ErroProvedorLLM, ErroRespostaLLMInvalida
from pfcompara.infraestrutura.llm.prompts import PROMPT_EXTRACAO_APOLICE


class ClienteOllama:
    """Integra a aplicação a um modelo local servido pelo Ollama."""

    def __init__(self, settings: Settings) -> None:
        """Armazena as configurações de conexão e modelo do Ollama."""

        self.settings = settings

    def extrair_apolice(self, texto: str) -> RespostaLLMExtracao:
        """Envia texto ao Ollama e valida a resposta JSON retornada."""

        schema = RespostaLLMExtracao.model_json_schema()
        payload = {
            "model": self.settings.ollama_model,
            "prompt": (
                f"{PROMPT_EXTRACAO_APOLICE}\n\n"
                "A resposta deve conter exatamente as chaves superiores apolice, "
                "confianca, requer_revisao_humana e justificativa.\n\n"
                f"TEXTO:\n{texto[:12000]}"
            ),
            "format": schema,
            "stream": False,
            "options": {"temperature": self.settings.llm_temperature},
        }
        try:
            resposta = httpx.post(
                f"{self.settings.ollama_base_url.rstrip('/')}/api/generate",
                json=payload,
                timeout=self.settings.llm_timeout_seconds,
            )
            resposta.raise_for_status()
            bruto = resposta.json().get("response", "{}")
            return RespostaLLMExtracao.model_validate(json.loads(bruto))
        except ValidationError as exc:
            raise ErroRespostaLLMInvalida("Ollama retornou JSON fora do schema esperado.") from exc
        except Exception as exc:
            raise ErroProvedorLLM(f"Falha ao chamar Ollama: {exc}") from exc
