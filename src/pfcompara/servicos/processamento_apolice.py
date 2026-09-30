"""Serviço de processamento de documento em apólice estruturada."""

from __future__ import annotations

from pfcompara.agentes.orquestrador import OrquestradorProcessamento
from pfcompara.infraestrutura.armazenamento.arquivos import ServicoArmazenamentoArquivos
from pfcompara.infraestrutura.banco.entidades import ApoliceORM
from pfcompara.infraestrutura.banco.repositorios import RepositorioApolices


class ServicoProcessamentoApolice:
    """Executa o processamento síncrono acionado pela API ou UI."""

    def __init__(self, repositorio: RepositorioApolices, armazenamento: ServicoArmazenamentoArquivos, orquestrador: OrquestradorProcessamento) -> None:
        """Recebe banco, armazenamento e orquestrador do processamento."""

        self.repositorio = repositorio
        self.armazenamento = armazenamento
        self.orquestrador = orquestrador

    def processar(self, documento_id: int, registrar=None) -> ApoliceORM:
        """Processa um documento existente e retorna a apólice gerada."""

        documento = self.repositorio.obter_documento(documento_id)
        if documento is None:
            raise ValueError("Documento não encontrado.")
        apolice_existente_id = documento.apolice.id if documento.apolice is not None else None
        resultado = self.orquestrador.processar(
            documento.id,
            self.armazenamento.caminho_documento(documento.nome_armazenado),
            registrar,
        )
        if apolice_existente_id is not None:
            comparacoes = self.repositorio.excluir_comparacoes_da_apolice(apolice_existente_id)
            self.armazenamento.excluir_relatorios(comparacoes)
            if registrar and comparacoes:
                registrar(
                    "[RepositorioApolices.excluir_comparacoes_da_apolice] Removendo comparações "
                    "anteriores, pois os dados da apólice foram atualizados."
                )
        return resultado
