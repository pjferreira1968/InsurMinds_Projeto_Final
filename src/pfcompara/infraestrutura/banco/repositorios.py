"""Repositórios SQLAlchemy para documentos, apólices e comparações.

Os repositórios isolam persistência das regras de negócio dos agentes. Novos
adaptadores podem implementar os mesmos métodos quando o projeto evoluir para
armazenamentos diferentes ou filas assíncronas.
"""

from __future__ import annotations

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from pfcompara.dominio.modelos import ApoliceEstruturada
from pfcompara.dominio.schemas_comparacao import ResultadoComparacao
from pfcompara.infraestrutura.banco.entidades import ApoliceORM, ComparacaoORM, DocumentoORM


class RepositorioApolices:
    """Persiste e consulta entidades centrais do PfCompara.

    Args:
        sessao: Sessão SQLAlchemy ativa, controlada pela camada de API ou script.
    """

    def __init__(self, sessao: Session) -> None:
        """Recebe a sessão transacional usada nas operações de persistência."""

        self.sessao = sessao

    def obter_documento_por_hash(self, hash_sha256: str) -> DocumentoORM | None:
        """Busca documento existente pelo hash criptográfico."""

        return self.sessao.scalar(select(DocumentoORM).where(DocumentoORM.hash_sha256 == hash_sha256))

    def obter_documento_por_nome(self, nome_original: str) -> DocumentoORM | None:
        """Busca o documento mais recente pelo nome original do upload."""

        return self.sessao.scalar(
            select(DocumentoORM)
            .where(DocumentoORM.nome_original == nome_original)
            .order_by(DocumentoORM.id.desc())
        )

    def salvar_documento(
        self, nome_original: str, nome_armazenado: str, hash_sha256: str, mime_type: str, tamanho_bytes: int
    ) -> DocumentoORM:
        """Persiste os metadados de um documento validado."""

        documento = DocumentoORM(
            nome_original=nome_original,
            nome_armazenado=nome_armazenado,
            hash_sha256=hash_sha256,
            mime_type=mime_type,
            tamanho_bytes=tamanho_bytes,
        )
        self.sessao.add(documento)
        self.sessao.commit()
        self.sessao.refresh(documento)
        return documento

    def atualizar_documento(self, documento_id: int, status: str, mensagem: str) -> None:
        """Atualiza estado funcional de processamento de um documento."""

        documento = self.sessao.get(DocumentoORM, documento_id)
        if documento is not None:
            documento.status = status
            documento.mensagem = mensagem
            self.sessao.commit()

    def obter_documento(self, documento_id: int) -> DocumentoORM | None:
        """Retorna um documento por identificador interno."""

        return self.sessao.get(DocumentoORM, documento_id)

    def salvar_apolice(
        self, documento_id: int, apolice: ApoliceEstruturada, texto_extraido: str
    ) -> ApoliceORM:
        """Persiste uma apólice estruturada e sua evidência textual."""

        existente = self.sessao.scalar(select(ApoliceORM).where(ApoliceORM.documento_id == documento_id))
        dados = apolice.model_dump(mode="json")
        if existente:
            existente.numero = apolice.numero
            existente.seguradora = apolice.seguradora
            existente.segurado = apolice.segurado
            existente.dados_estruturados = dados
            existente.texto_extraido = texto_extraido
            self.sessao.commit()
            self.sessao.refresh(existente)
            return existente
        registro = ApoliceORM(
            documento_id=documento_id,
            numero=apolice.numero,
            seguradora=apolice.seguradora,
            segurado=apolice.segurado,
            dados_estruturados=dados,
            texto_extraido=texto_extraido,
        )
        self.sessao.add(registro)
        self.sessao.commit()
        self.sessao.refresh(registro)
        return registro

    def listar_apolices(self) -> list[ApoliceORM]:
        """Lista apólices processadas em ordem decrescente de criação."""

        return list(self.sessao.scalars(select(ApoliceORM).order_by(ApoliceORM.id.desc())))

    def obter_apolice(self, apolice_id: int) -> ApoliceORM | None:
        """Retorna uma apólice por identificador interno."""

        return self.sessao.get(ApoliceORM, apolice_id)

    def excluir_comparacoes_da_apolice(self, apolice_id: int) -> list[int]:
        """Invalida comparações calculadas com uma versão anterior da apólice."""

        filtro = or_(
            ComparacaoORM.apolice_a_id == apolice_id,
            ComparacaoORM.apolice_b_id == apolice_id,
        )
        comparacao_ids = list(self.sessao.scalars(select(ComparacaoORM.id).where(filtro)))
        if comparacao_ids:
            self.sessao.execute(delete(ComparacaoORM).where(filtro))
            self.sessao.commit()
        return comparacao_ids

    def excluir_documento(self, documento_id: int) -> tuple[str, list[int]]:
        """Exclui documento, apólice e comparações dependentes em uma transação."""

        documento = self.obter_documento(documento_id)
        if documento is None:
            raise ValueError("Documento não encontrado.")

        comparacao_ids: list[int] = []
        if documento.apolice is not None:
            apolice_id = documento.apolice.id
            comparacao_ids = list(
                self.sessao.scalars(
                    select(ComparacaoORM.id).where(
                        or_(
                            ComparacaoORM.apolice_a_id == apolice_id,
                            ComparacaoORM.apolice_b_id == apolice_id,
                        )
                    )
                )
            )
            self.sessao.execute(
                delete(ComparacaoORM).where(
                    or_(
                        ComparacaoORM.apolice_a_id == apolice_id,
                        ComparacaoORM.apolice_b_id == apolice_id,
                    )
                )
            )
            self.sessao.delete(documento.apolice)

        nome_armazenado = documento.nome_armazenado
        self.sessao.delete(documento)
        self.sessao.commit()
        return nome_armazenado, comparacao_ids

    def salvar_comparacao(self, resultado: ResultadoComparacao) -> ComparacaoORM:
        """Persiste o resultado validado de uma comparação."""

        registro = ComparacaoORM(
            apolice_a_id=resultado.apolice_a_id,
            apolice_b_id=resultado.apolice_b_id,
            resultado=resultado.model_dump(mode="json"),
        )
        self.sessao.add(registro)
        self.sessao.commit()
        self.sessao.refresh(registro)
        return registro

    def obter_comparacao(self, comparacao_id: int) -> ComparacaoORM | None:
        """Retorna uma comparação persistida."""

        return self.sessao.get(ComparacaoORM, comparacao_id)
