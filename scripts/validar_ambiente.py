"""Valida as dependências básicas do ambiente local do produto."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
PACOTES = [
    "fastapi",
    "httpx",
    "streamlit",
    "sqlalchemy",
    "psycopg",
    "pydantic_settings",
    "pypdf",
    "pytesseract",
    "reportlab",
]


def _localizar_executavel(nome: str, caminho_alternativo: Path | None = None) -> str | None:
    """Localiza um executável no PATH ou em um caminho conhecido do Windows."""

    encontrado = shutil.which(nome)
    if encontrado:
        return encontrado
    if caminho_alternativo:
        try:
            if caminho_alternativo.is_file():
                return str(caminho_alternativo)
        except OSError:
            return str(caminho_alternativo)
    return None


def main() -> int:
    """Valida bibliotecas, Tesseract, Ollama e banco de dados."""

    os.chdir(RAIZ_PROJETO)
    sys.path.insert(0, str(RAIZ_PROJETO / "src"))
    problemas = 0

    print("Dependências Python")
    for pacote in PACOTES:
        encontrado = importlib.util.find_spec(pacote) is not None
        print(f"- {pacote}: {'ok' if encontrado else 'ausente'}")
        problemas += not encontrado

    if importlib.util.find_spec("sqlalchemy") and importlib.util.find_spec("pydantic_settings"):
        from sqlalchemy import text
        from sqlalchemy.engine import make_url
        from sqlalchemy.exc import SQLAlchemyError

        from insurminds_projeto_final.configuracao.settings import obter_settings
        from insurminds_projeto_final.infraestrutura.banco.conexao import engine

        settings = obter_settings()
        url_segura = make_url(settings.database_url).render_as_string(hide_password=True)
        try:
            with engine.connect() as conexao:
                conexao.execute(text("SELECT 1"))
            print(f"Banco de dados: ok ({url_segura})")
        except SQLAlchemyError as erro:
            print(f"Banco de dados: erro ({url_segura}) - {erro}")
            problemas += 1

        executavel = settings.tesseract_cmd or _localizar_executavel(
            "tesseract",
            Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        )
        if executavel:
            try:
                resultado = subprocess.run(
                    [executavel, "--version"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                print(f"Tesseract OCR: {'ok' if resultado.returncode == 0 else 'erro'}")
                problemas += resultado.returncode != 0
                idiomas = subprocess.run(
                    [executavel, "--list-langs"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                idiomas_instalados = {
                    linha.strip() for linha in idiomas.stdout.splitlines() if linha.strip()
                }
                idioma_ok = idiomas.returncode == 0 and settings.ocr_language in idiomas_instalados
                status_idioma = (
                    "ok"
                    if idioma_ok
                    else "ausente; instale o arquivo .traineddata conforme README.md"
                )
                print(
                    f"Idioma OCR {settings.ocr_language}: "
                    f"{status_idioma}"
                )
                problemas += not idioma_ok
            except OSError as erro:
                print(f"Tesseract OCR: erro ao executar {executavel} - {erro}")
                problemas += 1
        else:
            print("Tesseract OCR: não encontrado (configure TESSERACT_CMD no .env)")
            problemas += 1

        executavel_ollama = _localizar_executavel(
            "ollama",
            Path.home() / "AppData" / "Local" / "Programs" / "Ollama" / "ollama.exe",
        )
        if executavel_ollama:
            try:
                resultado = subprocess.run(
                    [executavel_ollama, "--version"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                print(f"Ollama CLI: {'ok' if resultado.returncode == 0 else 'erro'}")
                problemas += resultado.returncode != 0
            except OSError as erro:
                print(f"Ollama CLI: erro ao executar {executavel_ollama} - {erro}")
                problemas += 1
        else:
            print("Ollama CLI: não encontrado; instale o Ollama conforme README.md")
            problemas += 1

        if importlib.util.find_spec("httpx"):
            import httpx

            endpoint_modelos = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
            try:
                resposta = httpx.get(endpoint_modelos, timeout=5)
                resposta.raise_for_status()
                modelos = {
                    modelo.get("name") or modelo.get("model")
                    for modelo in resposta.json().get("models", [])
                }
                modelo_ok = settings.ollama_model in modelos
                status_modelo = (
                    "ok"
                    if modelo_ok
                    else f"não instalado; execute: ollama pull {settings.ollama_model}"
                )
                print(f"Ollama API: ok ({settings.ollama_base_url})")
                print(
                    f"Modelo Ollama {settings.ollama_model}: "
                    f"{status_modelo}"
                )
                problemas += not modelo_ok
            except (httpx.HTTPError, ValueError) as erro:
                print(
                    f"Ollama API: indisponível em {settings.ollama_base_url}; "
                    f"inicie o Ollama ou execute 'ollama serve' - {erro}"
                )
                problemas += 1

    return 1 if problemas else 0


if __name__ == "__main__":
    raise SystemExit(main())
