"""Componente visual para explicar a seleção de LLM."""

from __future__ import annotations

import streamlit as st


def mostrar_provedor_llm(provedor: str) -> None:
    """Apresenta o provedor configurado sem expor credenciais."""

    st.caption(f"Provedor LLM configurado: {provedor}. Ajuste LLM_PROVIDER no arquivo .env.")
