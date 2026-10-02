"""Constantes funcionais compartilhadas pela aplicação InsurMinds_Projeto_Final.

Este módulo concentra valores estáveis do domínio, como extensões aceitas,
categorias de cláusulas D&O e mensagens padronizadas. Manter esses valores em
um único ponto reduz divergências entre API, UI, agentes e testes.
"""

from __future__ import annotations

EMPRESA_PRODUTO = "IA4Seg"
NOME_PRODUTO = "InsurMinds_Projeto_Final"
EXTENSOES_PERMITIDAS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
MIME_TYPES_PERMITIDOS = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/tiff",
}
CATEGORIAS_CLAUSULAS = [
    "dados_apolice",
    "seguradora",
    "segurado",
    "vigencia",
    "limites",
    "sublimites",
    "franquias",
    "coberturas",
    "extensoes",
    "exclusoes",
    "definicoes",
    "obrigacoes",
    "aviso_sinistro",
    "clausulas_particulares",
]
AVISO_REVISAO_HUMANA = (
    "Os resultados apoiam a análise e devem ser validados por especialistas em seguros, "
    "corretores, subscritores ou assessoria jurídica."
)
