"""Agente de persistência de apólices estruturadas e evidências."""

from __future__ import annotations

from pfcompara.dominio.modelos import ApoliceEstruturada
from pfcompara.infraestrutura.banco.entidades import ApoliceORM
from pfcompara.infraestrutura.banco.repositorios import RepositorioApolices


class AgentePersistencia:
    """Grava os dados estruturados no banco com transação controlada."""

    def __init__(self, repositorio: RepositorioApolices) -> None:
        """Recebe o repositório usado para gravar a apólice estruturada."""

        self.repositorio = repositorio

    def salvar_apolice(self, documento_id: int, apolice: ApoliceEstruturada, texto_extraido: str) -> ApoliceORM:
        """Persiste uma apólice vinculada ao documento original."""

        return self.repositorio.salvar_apolice(documento_id, apolice, texto_extraido)
