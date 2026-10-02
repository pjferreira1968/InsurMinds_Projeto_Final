"""Aplicação FastAPI do InsurMinds_Projeto_Final.

Instancia a API REST, registra as rotas do MVP e cria as tabelas ausentes a
partir dos modelos SQLAlchemy.
"""

from __future__ import annotations

from fastapi import FastAPI

from insurminds_projeto_final.api.routers import apolices, comparacoes, documentos, relatorios, saude
from insurminds_projeto_final.configuracao.logging import configurar_logging
from insurminds_projeto_final.configuracao.settings import obter_settings
from insurminds_projeto_final.infraestrutura.banco.conexao import criar_tabelas

settings = obter_settings()
configurar_logging(settings.log_level)
criar_tabelas()

app = FastAPI(
    title="InsurMinds_Projeto_Final",
    description="Plataforma Inteligente para Análise e Comparação de Apólices D&O.",
    version="0.1.0",
)
app.include_router(saude.router)
app.include_router(documentos.router)
app.include_router(apolices.router)
app.include_router(comparacoes.router)
app.include_router(relatorios.router)
