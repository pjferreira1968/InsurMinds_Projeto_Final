"""Exclusão coordenada de apólices e seus artefatos derivados."""

from __future__ import annotations

from pfcompara.infraestrutura.armazenamento.arquivos import ServicoArmazenamentoArquivos
from pfcompara.infraestrutura.banco.repositorios import RepositorioApolices


class ServicoGestaoApolices:
    """Remove uma apólice, o documento de origem e suas comparações."""

    def __init__(
        self,
        repositorio: RepositorioApolices,
        armazenamento: ServicoArmazenamentoArquivos,
    ) -> None:
        """Recebe os componentes que removem registros e arquivos relacionados."""

        self.repositorio = repositorio
        self.armazenamento = armazenamento

    def excluir(self, apolice_id: int) -> None:
        """Executa a exclusão lógica e física relacionada à apólice."""

        apolice = self.repositorio.obter_apolice(apolice_id)
        if apolice is None:
            raise ValueError("Apólice não encontrada.")
        nome_armazenado, comparacao_ids = self.repositorio.excluir_documento(apolice.documento_id)
        self.armazenamento.excluir(nome_armazenado)
        self.armazenamento.excluir_relatorios(comparacao_ids)
