"""Interface Streamlit para importação, gestão e comparação de apólices D&O."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

RAIZ_SRC = str(Path(__file__).resolve().parents[2])
if RAIZ_SRC in sys.path:
    sys.path.remove(RAIZ_SRC)
sys.path.insert(0, RAIZ_SRC)

from insurminds_projeto_final.api.dependencies import criar_servicos
from insurminds_projeto_final.configuracao.constantes import EMPRESA_PRODUTO, NOME_PRODUTO
from insurminds_projeto_final.configuracao.settings import obter_settings
from insurminds_projeto_final.dominio.enums import ClassificacaoComparacao, ModoComparacao
from insurminds_projeto_final.dominio.schemas_comparacao import ResultadoComparacao
from insurminds_projeto_final.excecoes import ErroInsurMinds_Projeto_Final
from insurminds_projeto_final.infraestrutura.banco.conexao import SessionLocal, criar_tabelas
from insurminds_projeto_final.servicos.log_execucao import LogExecucao
from insurminds_projeto_final.ui.componentes.alertas import aviso_revisao_humana
from insurminds_projeto_final.ui.componentes.seletor_llm import mostrar_provedor_llm
from insurminds_projeto_final.ui.componentes.tabelas import tabela_apolices


ROTULOS_CLASSIFICACAO = {
    ClassificacaoComparacao.EQUIVALENTE.value: "Equivalente",
    ClassificacaoComparacao.DIFERENTE.value: "Diferente",
    ClassificacaoComparacao.AUSENTE_A.value: "Ausente na apólice A",
    ClassificacaoComparacao.AUSENTE_B.value: "Ausente na apólice B",
    ClassificacaoComparacao.INDETERMINADO.value: "Não identificado",
    ClassificacaoComparacao.NAO_ENCONTRADO.value: "Não encontrado",
}


def rotulo_apolice(apolice) -> str:
    """Monta uma identificação inequívoca para seletores e resultados."""

    numero = apolice.numero or "sem número"
    seguradora = apolice.seguradora or "seguradora não identificada"
    return f"#{apolice.id} | {numero} | {seguradora} | {apolice.documento.nome_original}"


def normalizar_id_selecionado(
    ids_disponiveis: list[int], id_atual: int | None, ids_excluidos: set[int] | None = None
) -> int:
    """Mantém uma seleção persistida somente quando ela ainda é válida."""

    excluidos = ids_excluidos or set()
    validos = [item for item in ids_disponiveis if item not in excluidos]
    if not validos:
        raise ValueError("Não há opções disponíveis para seleção.")
    return id_atual if id_atual in validos else validos[0]


def criar_log_visual(titulo: str) -> LogExecucao:
    """Cria uma área atualizável para acompanhar uma operação."""

    st.markdown(f"#### {titulo}")
    area = st.empty()

    def atualizar(mensagens: list[str]) -> None:
        """Substitui o conteúdo visual do log pelas mensagens acumuladas."""

        area.code("\n".join(mensagens), language=None)

    return LogExecucao(atualizar)


def mostrar_detalhes(apolice) -> None:
    """Apresenta dados estruturados sem expor JSON ao usuário final."""

    dados = apolice.dados_estruturados
    colunas = st.columns(3)
    colunas[0].metric("Número", dados.get("numero") or "Não identificado")
    colunas[1].metric("Seguradora", dados.get("seguradora") or "Não identificada")
    colunas[2].metric("Segurado", dados.get("segurado") or "Não identificado")

    for titulo, chave in (("Limites", "limites"), ("Franquias", "franquias")):
        st.markdown(f"**{titulo}**")
        registros = dados.get(chave, [])
        if registros:
            st.dataframe(pd.DataFrame(registros).drop(columns=["evidencia"], errors="ignore"), width="stretch")
        else:
            st.caption(f"Nenhum item de {titulo.lower()} foi identificado.")


def mostrar_resultado(resultado: ResultadoComparacao) -> None:
    """Exibe a comparação em linguagem de negócio e formato escaneável."""

    st.markdown("### Resultado da comparação")
    col_a, col_b = st.columns(2)
    col_a.markdown(f"**Apólice A**  \n{resultado.apolice_a_nome}")
    col_b.markdown(f"**Apólice B**  \n{resultado.apolice_b_nome}")

    divergentes = [
        item for item in resultado.itens if item.classificacao != ClassificacaoComparacao.EQUIVALENTE
    ]
    m1, m2, m3 = st.columns(3)
    m1.metric("Critérios analisados", len(resultado.itens))
    m2.metric("Divergências", len(divergentes))
    m3.metric("Modo", resultado.modo.value.capitalize())

    if resultado.modo == ModoComparacao.RELEVANTE:
        st.markdown("#### Parecer ponderado")
        if resultado.pontos_relevantes_selecionados:
            st.caption(
                "Pontos selecionados: "
                + "; ".join(resultado.pontos_relevantes_selecionados)
            )
        st.info(resultado.parecer)
        pontos_a, pontos_b = st.columns(2)
        pontos_a.metric("Pontuação da Apólice A", f"{resultado.pontuacao_apolice_a:g}")
        pontos_b.metric("Pontuação da Apólice B", f"{resultado.pontuacao_apolice_b:g}")

    linhas = [
        {
            "Categoria": item.categoria.replace("_", " ").title(),
            "Ponto relevante": item.criterio_relevante or item.campo,
            "Critério analisado": item.campo,
            "Apólice A": item.valor_apolice_a or "Não identificado",
            "Apólice B": item.valor_apolice_b or "Não identificado",
            "Conclusão": ROTULOS_CLASSIFICACAO[item.classificacao.value],
            "Peso": f"{item.peso:g}" if item.peso else "-",
            "Impacto": item.impacto,
        }
        for item in resultado.itens
    ]
    classificacoes = [item.classificacao for item in resultado.itens]
    cores = {
        ClassificacaoComparacao.EQUIVALENTE: "background-color: #CFE8FF; color: #123A5A",
        ClassificacaoComparacao.DIFERENTE: "background-color: #FFE08A; color: #4A3500",
        ClassificacaoComparacao.AUSENTE_A: "background-color: #F7B7C3; color: #5B1724",
        ClassificacaoComparacao.AUSENTE_B: "background-color: #F7B7C3; color: #5B1724",
        ClassificacaoComparacao.INDETERMINADO: "background-color: #D7DCE2; color: #26313D",
        ClassificacaoComparacao.NAO_ENCONTRADO: "background-color: #E2C6F2; color: #3F1557",
    }

    st.markdown("#### Quadro comparativo")
    st.markdown(
        """
        <div style="display:flex;gap:18px;flex-wrap:wrap;margin:0 0 10px 0;font-size:0.9rem">
          <span><b style="display:inline-block;width:12px;height:12px;background:#CFE8FF;border:1px solid #3B82B8"></b> Equivalente</span>
          <span><b style="display:inline-block;width:12px;height:12px;background:#FFE08A;border:1px solid #B77900"></b> Diferente</span>
          <span><b style="display:inline-block;width:12px;height:12px;background:#F7B7C3;border:1px solid #B74458"></b> Ausente em uma apólice</span>
          <span><b style="display:inline-block;width:12px;height:12px;background:#D7DCE2;border:1px solid #667085"></b> Não identificado</span>
          <span><b style="display:inline-block;width:12px;height:12px;background:#E2C6F2;border:1px solid #7B3F98"></b> Não encontrado</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabela = pd.DataFrame(linhas)

    def destacar_linha(linha):
        """Aplica à linha a cor correspondente à classificação do item."""

        estilo = cores[classificacoes[linha.name]]
        return [estilo] * len(linha)

    st.dataframe(tabela.style.apply(destacar_linha, axis=1), width="stretch", hide_index=True)


def main() -> None:
    """Renderiza a experiência principal do InsurMinds_Projeto_Final."""

    criar_tabelas()
    settings = obter_settings()
    st.set_page_config(page_title=f"{NOME_PRODUTO} | {EMPRESA_PRODUTO}", layout="wide")
    st.markdown(
        f'<div style="color:#0F766E;font-size:1rem;font-weight:700;margin-bottom:-0.4rem">'
        f'{EMPRESA_PRODUTO}</div>',
        unsafe_allow_html=True,
    )
    st.title(NOME_PRODUTO)
    st.caption("Análise e comparação de apólices D&O com OCR, IA Generativa e revisão humana.")
    aviso_revisao_humana()
    mostrar_provedor_llm(settings.llm_provider)
    abas = st.tabs(["Importar", "Apólices importadas", "Comparar", "Sobre"])

    with SessionLocal() as sessao:
        servicos = criar_servicos(sessao)

        with abas[0]:
            st.subheader("Importar apólice")
            st.caption("Um novo arquivo com o mesmo nome substitui integralmente a versão anterior.")
            arquivo = st.file_uploader(
                "Selecione um PDF ou uma imagem",
                type=["pdf", "png", "jpg", "jpeg", "tif", "tiff"],
            )
            if arquivo and st.button("Importar e processar", type="primary", icon=":material/upload_file:"):
                log = criar_log_visual("Log da importação")
                try:
                    documento = servicos["ingestao"].enviar(
                        arquivo.name,
                        arquivo.getvalue(),
                        arquivo.type,
                        log.registrar,
                    )
                    apolice = servicos["processamento"].processar(documento.id, log.registrar)
                    st.success(f"Apólice importada com sucesso. Identificador: {apolice.id}")
                except ErroInsurMinds_Projeto_Final as exc:
                    st.error(f"Não foi possível processar o documento: {exc}")
                except Exception:
                    st.error("O processamento falhou inesperadamente. Consulte os logs e tente novamente.")

        with abas[1]:
            st.subheader("Apólices importadas")
            apolices = servicos["consulta"].listar()
            if apolices:
                apolices_por_id = {item.id: item for item in apolices}
                ids_apolices = list(apolices_por_id)
                rotulos_por_id = {
                    item_id: rotulo_apolice(item) for item_id, item in apolices_por_id.items()
                }
                versao_grid = st.session_state.get("versao_grid_apolices", 0)
                ids_para_excluir = tabela_apolices(apolices, f"grid_apolices_{versao_grid}")
                if st.button(
                    "Excluir selecionadas",
                    icon=":material/delete:",
                    disabled=not ids_para_excluir,
                ):
                    st.session_state["ids_exclusao_pendente"] = ids_para_excluir

                ids_pendentes = st.session_state.get("ids_exclusao_pendente", [])
                if ids_pendentes:
                    selecionadas = [item for item in apolices if item.id in ids_pendentes]
                    nomes = ", ".join(item.documento.nome_original for item in selecionadas)
                    st.warning(
                        f"Confirme a exclusão de {len(selecionadas)} apólice(s): {nomes}. "
                        "Também serão removidos os arquivos, comparações e relatórios vinculados."
                    )
                    confirmar, cancelar, _ = st.columns([1, 1, 4])
                    if confirmar.button("Confirmar exclusão", type="primary", icon=":material/delete_forever:"):
                        try:
                            for item in selecionadas:
                                servicos["gestao"].excluir(item.id)
                            st.session_state.pop("ids_exclusao_pendente", None)
                            st.session_state["versao_grid_apolices"] = versao_grid + 1
                            st.success("Apólices e informações relacionadas foram excluídas.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Não foi possível concluir a exclusão: {exc}")
                    if cancelar.button("Cancelar"):
                        st.session_state.pop("ids_exclusao_pendente", None)
                        st.rerun()

                st.markdown("#### Consultar detalhes")
                st.session_state["consulta_apolice_id"] = normalizar_id_selecionado(
                    ids_apolices,
                    st.session_state.get("consulta_apolice_id"),
                )
                selecionada_id = st.selectbox(
                    "Selecione uma apólice",
                    ids_apolices,
                    format_func=rotulos_por_id.get,
                    key="consulta_apolice_id",
                )
                selecionada = apolices_por_id[selecionada_id]
                mostrar_detalhes(selecionada)
            else:
                st.session_state.pop("consulta_apolice_id", None)
                st.info("Nenhuma apólice foi importada.")

        with abas[2]:
            st.subheader("Comparar apólices")
            apolices = servicos["consulta"].listar()
            if len(apolices) < 2:
                st.info("Importe pelo menos duas apólices para iniciar uma comparação.")
            else:
                apolices_por_id = {item.id: item for item in apolices}
                ids_apolices = list(apolices_por_id)
                rotulos_por_id = {
                    item_id: rotulo_apolice(item) for item_id, item in apolices_por_id.items()
                }
                modo_texto = st.radio(
                    "Escopo da comparação",
                    ["C Completa", "R Relevante"],
                    horizontal=True,
                    help="Completa considera todos os campos extraídos. Relevante usa os critérios configurados em config/pontos_relevantes.json.",
                    key="comparacao_modo",
                )
                modo = (
                    ModoComparacao.COMPLETA
                    if modo_texto.startswith("C")
                    else ModoComparacao.RELEVANTE
                )
                pontos_relevantes_ids: list[str] = []
                if modo == ModoComparacao.RELEVANTE:
                    pontos_configurados = servicos["comparacao"].listar_pontos_relevantes()
                    pontos_por_id = {
                        ponto["id"]: ponto for ponto in pontos_configurados if ponto.get("id")
                    }
                    ids_pontos = list(pontos_por_id)
                    selecao_atual = st.session_state.get("comparacao_pontos_relevantes")
                    if selecao_atual is None:
                        selecao_atual = ids_pontos
                    st.session_state["comparacao_pontos_relevantes"] = [
                        item_id for item_id in selecao_atual if item_id in pontos_por_id
                    ]
                    pontos_relevantes_ids = st.multiselect(
                        "Pontos relevantes",
                        ids_pontos,
                        format_func=lambda item_id: pontos_por_id[item_id].get("rotulo", item_id),
                        key="comparacao_pontos_relevantes",
                        placeholder="Selecione ao menos um ponto relevante",
                    )
                    if not pontos_relevantes_ids:
                        st.error("Selecione ao menos um ponto relevante para realizar a comparação.")
                col_a, col_b = st.columns(2)
                st.session_state["comparacao_a_id"] = normalizar_id_selecionado(
                    ids_apolices,
                    st.session_state.get("comparacao_a_id"),
                )
                apolice_a_id = col_a.selectbox(
                    "Apólice A",
                    ids_apolices,
                    format_func=rotulos_por_id.get,
                    key="comparacao_a_id",
                )
                apolice_a = apolices_por_id[apolice_a_id]
                opcoes_b = [item_id for item_id in ids_apolices if item_id != apolice_a_id]
                st.session_state["comparacao_b_id"] = normalizar_id_selecionado(
                    ids_apolices,
                    st.session_state.get("comparacao_b_id"),
                    {apolice_a_id},
                )
                apolice_b_id = col_b.selectbox(
                    "Apólice B",
                    opcoes_b,
                    format_func=rotulos_por_id.get,
                    key="comparacao_b_id",
                )
                apolice_b = apolices_por_id[apolice_b_id]
                col_a.info(rotulo_apolice(apolice_a))
                col_b.info(rotulo_apolice(apolice_b))

                assinatura = (
                    apolice_a_id,
                    apolice_b_id,
                    modo.value,
                    tuple(pontos_relevantes_ids),
                )
                resultado_salvo = st.session_state.get("ultima_comparacao")
                if resultado_salvo and resultado_salvo["assinatura"] != assinatura:
                    st.session_state.pop("ultima_comparacao", None)
                    resultado_salvo = None

                if st.button(
                    "Comparar apólices",
                    type="primary",
                    icon=":material/compare_arrows:",
                    disabled=modo == ModoComparacao.RELEVANTE and not pontos_relevantes_ids,
                ):
                    log = criar_log_visual("Log da comparação")
                    try:
                        comparacao = servicos["comparacao"].comparar(
                            apolice_a.id,
                            apolice_b.id,
                            modo,
                            log.registrar,
                            pontos_relevantes_ids=pontos_relevantes_ids,
                        )
                        resultado = ResultadoComparacao.model_validate(comparacao.resultado)
                        log.registrar(
                            "[ServicoGeracaoRelatorio.gerar] Gerando relatório comparativo em PDF."
                        )
                        _, pdf = servicos["relatorio"].gerar(comparacao.id)
                        log.registrar(
                            "[ServicoGeracaoRelatorio.gerar] Relatório PDF disponível para download."
                        )
                        resultado_salvo = {
                            "assinatura": assinatura,
                            "resultado": resultado.model_dump(mode="json"),
                            "pdf": pdf.read_bytes(),
                            "nome_pdf": pdf.name,
                        }
                        st.session_state["ultima_comparacao"] = resultado_salvo
                    except Exception as exc:
                        st.error(f"Não foi possível concluir a comparação: {exc}")

                if resultado_salvo:
                    mostrar_resultado(
                        ResultadoComparacao.model_validate(resultado_salvo["resultado"])
                    )
                    st.download_button(
                        "Baixar relatório PDF",
                        resultado_salvo["pdf"],
                        file_name=resultado_salvo["nome_pdf"],
                        mime="application/pdf",
                        icon=":material/download:",
                    )

        with abas[3]:
            st.markdown(
                """
                **Arquitetura:** FastAPI, Streamlit, SQLAlchemy, PostgreSQL ou SQLite,
                OCR local com Tesseract e LLM configurável por Ollama ou OpenAI.

                **Produto:** InsurMinds_Projeto_Final é desenvolvido e mantido pela IA4Seg.

                **Uso responsável:** o resultado apoia a triagem e a comparação, mas não
                substitui a análise de corretores, subscritores ou profissionais jurídicos.
                """
            )


if __name__ == "__main__":
    main()
