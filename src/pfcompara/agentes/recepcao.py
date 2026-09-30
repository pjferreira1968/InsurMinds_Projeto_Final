"""Agente responsável pela recepção segura de documentos."""

from __future__ import annotations

from pfcompara.excecoes import ErroDocumentoInvalido
from pfcompara.infraestrutura.armazenamento.arquivos import ServicoArmazenamentoArquivos
from pfcompara.infraestrutura.banco.entidades import DocumentoORM
from pfcompara.infraestrutura.banco.repositorios import RepositorioApolices


class AgenteRecepcao:
    """Valida upload, calcula hash, detecta duplicidade e registra documento."""

    def __init__(self, armazenamento: ServicoArmazenamentoArquivos, repositorio: RepositorioApolices) -> None:
        """Recebe os componentes de arquivos e banco usados na importação."""

        self.armazenamento = armazenamento
        self.repositorio = repositorio

    def receber(
        self,
        nome_original: str,
        conteudo: bytes,
        mime_type: str | None,
        registrar=None,
    ) -> DocumentoORM:
        """Recebe um arquivo do usuário e persiste seus metadados seguros."""

        if registrar:
            registrar(f"[AgenteRecepcao.receber] Iniciando importação do arquivo {nome_original}.")
        hash_sha256, tamanho, mime, extensao = self.armazenamento.validar(nome_original, conteudo, mime_type)
        if registrar:
            registrar(
                "[ServicoArmazenamentoArquivos.validar] Executando verificação de formato, "
                "tamanho, tipo MIME e integridade."
            )

        existente_nome = self.repositorio.obter_documento_por_nome(nome_original)
        existente_hash = self.repositorio.obter_documento_por_hash(hash_sha256)
        if existente_hash and (existente_nome is None or existente_hash.id != existente_nome.id):
            raise ErroDocumentoInvalido("Documento duplicado: já existe arquivo com o mesmo hash.")

        nome_armazenado = self.armazenamento.salvar(conteudo, extensao)
        if existente_nome:
            if registrar:
                registrar(
                    "[RepositorioApolices.excluir_documento] Nome já existente; removendo dados "
                    "e comparações da versão anterior."
                )
            antigo, comparacoes = self.repositorio.excluir_documento(existente_nome.id)
            self.armazenamento.excluir(antigo)
            self.armazenamento.excluir_relatorios(comparacoes)

        if registrar:
            registrar(
                "[RepositorioApolices.salvar_documento] Armazenando o arquivo validado e "
                "registrando seus metadados."
            )
        return self.repositorio.salvar_documento(nome_original, nome_armazenado, hash_sha256, mime, tamanho)
