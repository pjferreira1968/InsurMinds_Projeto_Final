"""Cliente real para API OpenAI compatível com o MVP."""

from __future__ import annotations

import json

import httpx
from pydantic import ValidationError

from insurminds_projeto_final.configuracao.settings import Settings
from insurminds_projeto_final.dominio.schemas_extracao import RespostaLLMExtracao
from insurminds_projeto_final.excecoes import ErroProvedorLLM, ErroRespostaLLMInvalida
from insurminds_projeto_final.infraestrutura.llm.prompts import PROMPT_EXTRACAO_APOLICE


class ClienteOpenAI:
    """Integra a aplicação à API paga da OpenAI quando configurada."""

    def __init__(self, settings: Settings) -> None:
        """Armazena as configurações de autenticação e modelo da OpenAI."""

        self.settings = settings

    def extrair_apolice(self, texto: str) -> RespostaLLMExtracao:
        """Solicita extração estruturada por Chat Completions em JSON."""

        if not self.settings.openai_api_key:
            raise ErroProvedorLLM("OPENAI_API_KEY não foi configurada.")
        payload = {
            "model": self.settings.openai_model,
            "temperature": self.settings.llm_temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": PROMPT_EXTRACAO_APOLICE},
                {"role": "user", "content": texto[:12000]},
            ],
        }
        headers = {"Authorization": f"Bearer {self.settings.openai_api_key}"}
        try:
            resposta = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.settings.llm_timeout_seconds,
            )
            resposta.raise_for_status()
            conteudo = resposta.json()["choices"][0]["message"]["content"]
            return RespostaLLMExtracao.model_validate(json.loads(conteudo))
        except ValidationError as exc:
            raise ErroRespostaLLMInvalida("OpenAI retornou JSON fora do schema esperado.") from exc
        except Exception as exc:
            raise ErroProvedorLLM(f"Falha ao chamar OpenAI: {exc}") from exc
