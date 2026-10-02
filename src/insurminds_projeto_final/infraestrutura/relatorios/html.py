"""Geração de relatório HTML comparativo."""

from __future__ import annotations

from pathlib import Path

from insurminds_projeto_final.configuracao.constantes import AVISO_REVISAO_HUMANA, EMPRESA_PRODUTO, NOME_PRODUTO
from insurminds_projeto_final.dominio.schemas_comparacao import ResultadoComparacao


class GeradorRelatorioHTML:
    """Renderiza uma comparação em HTML simples, auditável e exportável."""

    def gerar(self, resultado: ResultadoComparacao, caminho: Path) -> Path:
        """Gera arquivo HTML com resumo, tabela de diferenças e aviso obrigatório."""

        classes = {
            "equivalente": "equivalente",
            "diferente": "diferente",
            "ausente_na_apolice_a": "ausente",
            "ausente_na_apolice_b": "ausente",
            "indeterminado": "indeterminado",
            "nao_encontrado": "nao-encontrado",
        }
        linhas = "\n".join(
            f'<tr class="{classes[i.classificacao.value]}"><td>{i.categoria}</td><td>{i.criterio_relevante or i.campo}</td><td>{i.campo}</td><td>{i.valor_apolice_a or ""}</td><td>{i.valor_apolice_b or ""}</td><td>{i.classificacao}</td><td>{i.peso:g}</td><td>{i.impacto}</td></tr>'
            for i in resultado.itens
        )
        html = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>{NOME_PRODUTO} | {EMPRESA_PRODUTO}</title>
<style>body{{font-family:Arial,sans-serif;margin:40px;color:#1f2937}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #9aa4b2;padding:8px;vertical-align:top}}th{{background:#17324d;color:white}}.aviso{{border-left:4px solid #b45309;padding:10px;background:#fff7ed}}.legenda{{display:flex;gap:18px;margin:12px 0}}.legenda span{{padding:5px 9px;border:1px solid #667085}}.equivalente{{background:#cfe8ff}}.diferente{{background:#ffe08a}}.ausente{{background:#f7b7c3}}.indeterminado{{background:#d7dce2}}.nao-encontrado{{background:#e2c6f2}}</style></head>
<body><p style="color:#0f766e;font-weight:bold">{EMPRESA_PRODUTO}</p><h1>Relatório Comparativo {NOME_PRODUTO}</h1><p>{resultado.resumo}</p><p><b>Pontos relevantes selecionados:</b> {'; '.join(resultado.pontos_relevantes_selecionados)}</p><h2>Parecer ponderado</h2><p>{resultado.parecer}</p><p><b>Pontuação A:</b> {resultado.pontuacao_apolice_a:g} | <b>Pontuação B:</b> {resultado.pontuacao_apolice_b:g}</p><div class="aviso">{AVISO_REVISAO_HUMANA}</div>
<h2>Quadro comparativo</h2><div class="legenda"><span class="equivalente">Equivalente</span><span class="diferente">Diferente</span><span class="ausente">Ausente em uma apólice</span><span class="indeterminado">Não identificado</span><span class="nao-encontrado">Não encontrado</span></div><table><thead><tr><th>Categoria</th><th>Ponto relevante</th><th>Critério analisado</th><th>Apólice A</th><th>Apólice B</th><th>Classificação</th><th>Peso</th><th>Impacto</th></tr></thead><tbody>{linhas}</tbody></table></body></html>"""
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(html, encoding="utf-8")
        return caminho
