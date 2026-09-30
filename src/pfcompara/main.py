"""Ponto de entrada CLI simplificado do PfCompara."""

from __future__ import annotations

import uvicorn

from pfcompara.configuracao.settings import obter_settings


def main() -> None:
    """Inicia a API FastAPI com parâmetros do ambiente."""

    settings = obter_settings()
    uvicorn.run("pfcompara.api.app:app", host=settings.app_host, port=settings.app_port, reload=True)


if __name__ == "__main__":
    main()
