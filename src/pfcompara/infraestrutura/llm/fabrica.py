"""Fábrica de clientes LLM configuráveis."""

from __future__ import annotations

from pfcompara.configuracao.settings import Settings
from pfcompara.infraestrutura.llm.heuristico import ClienteHeuristicoDemo
from pfcompara.infraestrutura.llm.ollama import ClienteOllama
from pfcompara.infraestrutura.llm.openai import ClienteOpenAI


def criar_cliente_llm(settings: Settings):
    """Retorna o cliente LLM selecionado por configuração."""

    provedor = settings.llm_provider.lower()
    if provedor == "ollama":
        return ClienteOllama(settings)
    if provedor == "openai":
        return ClienteOpenAI(settings)
    if provedor == "demo":
        return ClienteHeuristicoDemo()
    raise ValueError("LLM_PROVIDER deve ser 'ollama', 'openai' ou 'demo'.")
