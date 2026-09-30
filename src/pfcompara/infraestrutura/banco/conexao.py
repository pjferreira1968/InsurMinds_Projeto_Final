"""Criação de engine e sessões SQLAlchemy para o PfCompara."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from pfcompara.configuracao.settings import obter_settings
from pfcompara.infraestrutura.banco.entidades import Base


def criar_engine_banco():
    """Cria a engine SQLAlchemy a partir de `DATABASE_URL`.

    O parâmetro `check_same_thread` é aplicado apenas quando a URL aponta para
    SQLite, facilitando testes locais sem alterar o contrato PostgreSQL do MVP.
    """

    settings = obter_settings()
    kwargs = {"future": True}
    if settings.database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(settings.database_url, **kwargs)


engine = criar_engine_banco()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def criar_tabelas() -> None:
    """Cria as tabelas ausentes a partir dos modelos SQLAlchemy."""

    Base.metadata.create_all(bind=engine)


def obter_sessao() -> Iterator[Session]:
    """Fornece uma sessão transacional para dependências da API."""

    sessao = SessionLocal()
    try:
        yield sessao
    finally:
        sessao.close()
