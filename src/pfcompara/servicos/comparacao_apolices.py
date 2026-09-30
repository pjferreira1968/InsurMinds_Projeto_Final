"""Serviço de comparação de apólices."""

from __future__ import annotations

from pfcompara.agentes.comparacao import AgenteComparacao
from pfcompara.dominio.enums import ModoComparacao
from pfcompara.dominio.modelos import ApoliceEstruturada
from pfcompara.infraestrutura.banco.entidades import ComparacaoORM
from pfcompara.infraestrutura.banco.repositorios import RepositorioApolices


class ServicoComparacaoApolices:
    """Carrega apólices, compara dados e persiste resultado."""

    def __init__(self, repositorio: RepositorioApolices, agente: AgenteComparacao) -> None:
        """Recebe o repositório e o agente determinístico de comparação."""

        self.repositorio = repositorio
        self.agente = agente

    def comparar(
        self,
        apolice_a_id: int,
        apolice_b_id: int,
        modo: ModoComparacao = ModoComparacao.COMPLETA,
        registrar=None,
        pontos_relevantes_ids: list[str] | None = None,
    ) -> ComparacaoORM:
        """Compara duas apólices existentes."""

        if registrar:
            registrar(
                "[ServicoComparacaoApolices.comparar] Iniciando comparação e carregando as "
                "apólices selecionadas."
            )
        a = self.repositorio.obter_apolice(apolice_a_id)
        b = self.repositorio.obter_apolice(apolice_b_id)
        if a is None or b is None:
            raise ValueError("Uma das apólices informadas não foi encontrada.")
        if registrar:
            registrar(
                f"[ServicoComparacaoApolices.comparar] Validando seleção no modo {modo.value}."
            )
            registrar(
                "[AgenteComparacao.comparar] Comparando identificação, vigência, limites, "
                "franquias e cláusulas."
            )
        resultado = self.agente.comparar(
            a.id,
            ApoliceEstruturada.model_validate(a.dados_estruturados),
            b.id,
            ApoliceEstruturada.model_validate(b.dados_estruturados),
            modo,
            self._rotulo(a),
            self._rotulo(b),
            pontos_relevantes_ids,
        )
        if registrar:
            registrar(
                "[AgenteComparacao.comparar] Consolidando diferenças e pontos de atenção para revisão."
            )
        comparacao = self.repositorio.salvar_comparacao(resultado)
        if registrar:
            registrar(
                f"[RepositorioApolices.salvar_comparacao] Comparação concluída e armazenada "
                f"com ID {comparacao.id}."
            )
        return comparacao

    def listar_pontos_relevantes(self) -> list[dict]:
        """Lista os pontos pré-parametrizados disponíveis ao usuário."""

        return self.agente.listar_pontos_relevantes()

    @staticmethod
    def _rotulo(apolice) -> str:
        """Monta a identificação de negócio exibida para uma apólice."""

        numero = apolice.numero or "sem número identificado"
        seguradora = apolice.seguradora or "seguradora não identificada"
        return f"{numero} | {seguradora} | {apolice.documento.nome_original}"
