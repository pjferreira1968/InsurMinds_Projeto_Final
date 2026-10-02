"""Entidades SQLAlchemy persistidas no banco de dados principal.

SQLite é o banco padrão e PostgreSQL permanece disponível para ambientes que
necessitam de um servidor dedicado. Os campos JSON mantêm respostas estruturadas
de LLM, evidências e comparações com compatibilidade entre os dois bancos.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    """Base declarativa das entidades SQLAlchemy."""


class DocumentoORM(Base):
    """Documento recebido pela aplicação e seu estado de processamento."""

    __tablename__ = "documentos"
    __table_args__ = (UniqueConstraint("hash_sha256", name="uq_documentos_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome_original: Mapped[str] = mapped_column(String(255))
    nome_armazenado: Mapped[str] = mapped_column(String(255))
    hash_sha256: Mapped[str] = mapped_column(String(64), index=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    tamanho_bytes: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), index=True, default="recebido")
    mensagem: Mapped[str] = mapped_column(Text, default="Documento recebido.")
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    apolice: Mapped["ApoliceORM | None"] = relationship(back_populates="documento")


class ApoliceORM(Base):
    """Apólice D&O estruturada a partir de um documento processado."""

    __tablename__ = "apolices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    documento_id: Mapped[int] = mapped_column(ForeignKey("documentos.id"), index=True)
    numero: Mapped[str | None] = mapped_column(String(100), index=True)
    seguradora: Mapped[str | None] = mapped_column(String(255), index=True)
    segurado: Mapped[str | None] = mapped_column(String(255))
    dados_estruturados: Mapped[dict] = mapped_column(JSON)
    texto_extraido: Mapped[str] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    documento: Mapped[DocumentoORM] = relationship(back_populates="apolice")


class ComparacaoORM(Base):
    """Resultado persistido de uma comparação entre duas apólices."""

    __tablename__ = "comparacoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    apolice_a_id: Mapped[int] = mapped_column(ForeignKey("apolices.id"), index=True)
    apolice_b_id: Mapped[int] = mapped_column(ForeignKey("apolices.id"), index=True)
    resultado: Mapped[dict] = mapped_column(JSON)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
