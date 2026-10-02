"""Serviço de caso de uso para ingestão de documentos."""

from __future__ import annotations

from insurminds_projeto_final.agentes.recepcao import AgenteRecepcao
from insurminds_projeto_final.infraestrutura.banco.entidades import DocumentoORM


class ServicoIngestaoDocumento:
    """Expõe a recepção de documentos para API, UI e scripts."""

    def __init__(self, agente: AgenteRecepcao) -> None:
        """Recebe o agente responsável pela validação inicial do documento."""

        self.agente = agente

    def enviar(self, nome: str, conteudo: bytes, mime_type: str | None, registrar=None) -> DocumentoORM:
        """Envia um documento para validação e registro."""

        return self.agente.receber(nome, conteudo, mime_type, registrar)
