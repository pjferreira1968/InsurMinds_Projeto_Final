"""Ponto de entrada CLI simplificado do InsurMinds_Projeto_Final."""

from __future__ import annotations

import uvicorn

from insurminds_projeto_final.configuracao.settings import obter_settings


def main() -> None:
    """Inicia a API FastAPI com parâmetros do ambiente."""

    settings = obter_settings()
    uvicorn.run("insurminds_projeto_final.api.app:app", host=settings.app_host, port=settings.app_port, reload=True)


if __name__ == "__main__":
    main()
