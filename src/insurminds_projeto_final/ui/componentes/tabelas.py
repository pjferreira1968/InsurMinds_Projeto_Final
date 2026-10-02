"""Componentes tabulares da UI Streamlit."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def tabela_apolices(apolices: list[object], chave: str = "grid_apolices") -> list[int]:
    """Mostra apólices em um grid selecionável e retorna os IDs marcados."""

    dados = pd.DataFrame(
        [
            {
                "Excluir": False,
                "ID": a.id,
                "Arquivo": a.documento.nome_original,
                "Número": a.numero or "Não identificado",
                "Seguradora": a.seguradora or "Não identificada",
                "Segurado": a.segurado or "Não identificado",
                "Importado em": a.criado_em,
            }
            for a in apolices
        ]
    )
    editado = st.data_editor(
        dados,
        key=chave,
        width="stretch",
        hide_index=True,
        disabled=["ID", "Arquivo", "Número", "Seguradora", "Segurado", "Importado em"],
        column_config={
            "Excluir": st.column_config.CheckboxColumn(
                "Excluir",
                help="Marque as apólices que deseja excluir.",
                width="small",
            ),
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "Importado em": st.column_config.DatetimeColumn(
                "Importado em",
                format="DD/MM/YYYY HH:mm",
            ),
        },
    )
    return [int(valor) for valor in editado.loc[editado["Excluir"], "ID"].tolist()]
