"""Cliente real para Ollama local."""

from __future__ import annotations

import json

import httpx
from pydantic import ValidationError

from insurminds_projeto_final.configuracao.settings import Settings
from insurminds_projeto_final.dominio.schemas_extracao import RespostaLLMExtracao
from insurminds_projeto_final.excecoes import ErroProvedorLLM, ErroRespostaLLMInvalida
from insurminds_projeto_final.infraestrutura.llm.prompts import PROMPT_EXTRACAO_APOLICE


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
            "keep_alive": self.settings.ollama_keep_alive,
            "options": {"temperature": self.settings.llm_temperature},
        }
        try:
            timeout = httpx.Timeout(
                connect=10,
                read=self.settings.ollama_timeout_seconds,
                write=30,
                pool=10,
            )
            resposta = httpx.post(
                f"{self.settings.ollama_base_url.rstrip('/')}/api/generate",
                json=payload,
                timeout=timeout,
            )
            resposta.raise_for_status()
            bruto = resposta.json().get("response", "{}")
            return RespostaLLMExtracao.model_validate(json.loads(bruto))
        except ValidationError as exc:
            raise ErroRespostaLLMInvalida("Ollama retornou JSON fora do schema esperado.") from exc
        except httpx.TimeoutException as exc:
            raise ErroProvedorLLM(
                "Ollama excedeu o tempo máximo de "
                f"{self.settings.ollama_timeout_seconds} segundos. "
                "Aumente OLLAMA_TIMEOUT_SECONDS no arquivo .env se necessário."
            ) from exc
        except Exception as exc:
            raise ErroProvedorLLM(f"Falha ao chamar Ollama: {exc}") from exc
