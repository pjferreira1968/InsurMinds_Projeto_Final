"""Serviço de consulta de apólices processadas."""

from __future__ import annotations

from insurminds_projeto_final.infraestrutura.banco.entidades import ApoliceORM
from insurminds_projeto_final.infraestrutura.banco.repositorios import RepositorioApolices


class ServicoConsultaApolices:
    """Lista e detalha apólices disponíveis para comparação."""

    def __init__(self, repositorio: RepositorioApolices) -> None:
        """Recebe o repositório consultado pelo serviço."""

        self.repositorio = repositorio

    def listar(self) -> list[ApoliceORM]:
        """Lista apólices processadas."""

        return self.repositorio.listar_apolices()

    def obter(self, apolice_id: int) -> ApoliceORM | None:
        """Obtém detalhes de uma apólice."""

        return self.repositorio.obter_apolice(apolice_id)
