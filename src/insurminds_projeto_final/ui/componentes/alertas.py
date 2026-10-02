"""Componentes de alerta reutilizáveis da interface Streamlit."""

from __future__ import annotations

import streamlit as st

from insurminds_projeto_final.configuracao.constantes import AVISO_REVISAO_HUMANA


def aviso_revisao_humana() -> None:
    """Exibe aviso obrigatório de revisão humana especializada."""

    st.warning(AVISO_REVISAO_HUMANA)
