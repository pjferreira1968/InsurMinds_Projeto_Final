"""Valida dependências básicas do ambiente local."""

from __future__ import annotations

import importlib.util


def main() -> None:
    """Imprime situação das principais bibliotecas usadas pelo MVP."""

    for pacote in ["fastapi", "streamlit", "sqlalchemy", "pypdf", "pytesseract", "reportlab"]:
        status = "ok" if importlib.util.find_spec(pacote) else "ausente"
        print(f"{pacote}: {status}")


if __name__ == "__main__":
    main()
