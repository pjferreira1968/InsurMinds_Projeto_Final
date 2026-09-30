"""Modelos Pydantic centrais do domínio de apólices D&O.

As classes deste módulo representam dados estruturados extraídos das apólices,
evidências textuais e documentos persistidos. Elas são usadas por agentes,
serviços, API e relatórios para manter um contrato comum.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from pfcompara.dominio.enums import StatusDocumento


class Evidencia(BaseModel):
    """Trecho de documento que fundamenta uma informação estruturada."""

    texto: str = Field(..., min_length=1)
    pagina: int | None = None
    origem: str = "extração textual"


class Limite(BaseModel):
    """Limite ou sublimite financeiro de uma apólice D&O."""

    tipo: str
    valor: Decimal | None = None
    moeda: str = "BRL"
    descricao: str = ""
    evidencia: Evidencia | None = None


class Franquia(BaseModel):
    """Franquia, retenção ou participação obrigatória do segurado."""

    tipo: str
    valor: Decimal | None = None
    moeda: str = "BRL"
    descricao: str = ""
    evidencia: Evidencia | None = None


class Clausula(BaseModel):
    """Cláusula relevante identificada no documento."""

    categoria: str
    titulo: str
    conteudo: str
    evidencia: Evidencia | None = None


class ApoliceEstruturada(BaseModel):
    """Representação normalizada dos dados principais de uma apólice D&O."""

    numero: str | None = None
    seguradora: str | None = None
    segurado: str | None = None
    inicio_vigencia: date | None = None
    fim_vigencia: date | None = None
    limites: list[Limite] = Field(default_factory=list)
    franquias: list[Franquia] = Field(default_factory=list)
    coberturas: list[Clausula] = Field(default_factory=list)
    exclusoes: list[Clausula] = Field(default_factory=list)
    clausulas: list[Clausula] = Field(default_factory=list)
    aviso: str = ""


class DocumentoRecebido(BaseModel):
    """Metadados de um arquivo recebido e armazenado de modo seguro."""

    id: UUID = Field(default_factory=uuid4)
    nome_original: str
    nome_armazenado: str
    hash_sha256: str
    mime_type: str
    tamanho_bytes: int
    status: StatusDocumento = StatusDocumento.RECEBIDO
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    mensagem: str = "Documento recebido."


class ResultadoExtracao(BaseModel):
    """Resultado intermediário de extração textual e OCR."""

    texto: str
    metodo: Literal["pdf_textual", "ocr_tesseract", "texto_simples", "vazio"]
    paginas: int = 1
    observacoes: list[str] = Field(default_factory=list)
