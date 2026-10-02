"""Configurações da aplicação carregadas por variáveis de ambiente.

O módulo usa Pydantic Settings para validar parâmetros de banco, LLM, OCR e
armazenamento antes que os serviços sejam instanciados. Nenhuma chave secreta é
gravada em logs ou retornos de API.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Representa a configuração operacional validada do InsurMinds_Projeto_Final.

    Attributes:
        database_url: URL SQLAlchemy do banco principal.
        llm_provider: Provedor de LLM selecionado entre Ollama e OpenAI.
        storage_path: Diretório base para arquivos de entrada e relatórios.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "InsurMinds_Projeto_Final"
    app_env: str = "desenvolvimento"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    database_url: str = "sqlite:///./data/insurminds_projeto_final.sqlite"
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_timeout_seconds: int = Field(default=600, ge=30)
    ollama_keep_alive: str = "30m"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0
    llm_timeout_seconds: int = 120
    ocr_provider: str = "auto"
    ocr_language: str = "por"
    tesseract_cmd: str = ""
    max_upload_mb: int = Field(default=30, ge=1)
    storage_path: Path = Path("./data")


@lru_cache
def obter_settings() -> Settings:
    """Retorna uma instância cacheada das configurações da aplicação."""

    return Settings()
