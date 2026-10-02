"""Orquestra o processamento completo de documentos de apólices D&O.

Este módulo coordena extração de texto, identificação por LLM, estruturação e
persistência. Conteúdo integral de documentos não é registrado em logs para
reduzir exposição de dados sensíveis.
"""

from __future__ import annotations

from pathlib import Path

from insurminds_projeto_final.agentes.estruturacao import AgenteEstruturacao
from insurminds_projeto_final.agentes.extracao_texto import AgenteExtracaoTexto
from insurminds_projeto_final.agentes.identificacao_clausulas import AgenteIdentificacaoClausulas
from insurminds_projeto_final.agentes.persistencia import AgentePersistencia
from insurminds_projeto_final.infraestrutura.banco.entidades import ApoliceORM
from insurminds_projeto_final.infraestrutura.banco.repositorios import RepositorioApolices


class OrquestradorProcessamento:
    """Controla estados, transições e falhas do fluxo de processamento."""

    def __init__(
        self,
        repositorio: RepositorioApolices,
        extracao: AgenteExtracaoTexto,
        identificacao: AgenteIdentificacaoClausulas,
        estruturacao: AgenteEstruturacao,
        persistencia: AgentePersistencia,
    ) -> None:
        """Reúne os componentes executados sequencialmente na importação."""

        self.repositorio = repositorio
        self.extracao = extracao
        self.identificacao = identificacao
        self.estruturacao = estruturacao
        self.persistencia = persistencia

    def processar(self, documento_id: int, caminho: Path, registrar=None) -> ApoliceORM:
        """Executa o pipeline síncrono do MVP para um documento."""

        self.repositorio.atualizar_documento(documento_id, "processando", "Processamento iniciado.")
        try:
            if registrar:
                registrar(
                    "[AgenteExtracaoTexto.extrair] Extraindo o texto nativo ou executando OCR, "
                    "conforme o tipo do documento."
                )
            resultado_texto = self.extracao.extrair(caminho)
            if registrar:
                registrar(
                    "[AgenteIdentificacaoClausulas.identificar] Identificando campos, cláusulas, "
                    "limites e franquias com o provedor configurado."
                )
            resposta_llm = self.identificacao.identificar(resultado_texto.texto, registrar)
            if registrar:
                registrar(
                    "[AgenteEstruturacao.estruturar] Validando e normalizando os dados "
                    "estruturados da apólice."
                )
            apolice = self.estruturacao.estruturar(resposta_llm)
            if registrar:
                registrar(
                    "[AgentePersistencia.salvar_apolice] Armazenando a apólice estruturada e "
                    "suas evidências."
                )
            registro = self.persistencia.salvar_apolice(documento_id, apolice, resultado_texto.texto)
            self.repositorio.atualizar_documento(documento_id, "processado", "Documento processado com sucesso.")
            if registrar:
                registrar(
                    f"[OrquestradorProcessamento.processar] Importação concluída. "
                    f"Apólice registrada com ID {registro.id}."
                )
            return registro
        except Exception as exc:
            self.repositorio.atualizar_documento(documento_id, "falha", f"Falha no processamento: {exc}")
            if registrar:
                registrar(f"[OrquestradorProcessamento.processar] Importação interrompida: {exc}")
            raise
