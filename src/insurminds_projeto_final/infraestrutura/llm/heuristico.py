"""Extrator heurístico local para contingência e testes.

Este módulo não substitui uma LLM. Ele existe para que o MVP funcione com dados
quando Ollama ou OpenAI não estiverem disponíveis, sempre com aviso explícito
de revisão humana e baixa confiança.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation

from insurminds_projeto_final.configuracao.constantes import AVISO_REVISAO_HUMANA
from insurminds_projeto_final.dominio.modelos import ApoliceEstruturada, Clausula, Evidencia, Franquia, Limite
from insurminds_projeto_final.dominio.schemas_extracao import RespostaLLMExtracao


class ClienteHeuristicoDemo:
    """Extrai campos por padrões locais e marca o resultado para revisão."""

    def extrair_apolice(self, texto: str) -> RespostaLLMExtracao:
        """Produz uma estrutura mínima sem depender de provedor externo."""

        linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]

        def buscar(padrao: str) -> str | None:
            """Retorna o primeiro grupo capturado pelo padrão informado."""

            achado = re.search(padrao, texto, flags=re.IGNORECASE)
            return achado.group(1).strip() if achado else None

        def converter_moeda(valor: str | None) -> Decimal | None:
            """Converte valor brasileiro somente quando houver ao menos um dígito."""

            if not valor or not any(caractere.isdigit() for caractere in valor):
                return None
            try:
                return Decimal(valor.replace(".", "").replace(",", "."))
            except InvalidOperation:
                return None

        padrao_monetario = r"R\$\s*([0-9][0-9.]*(?:,[0-9]{2})?)"
        valor = buscar(
            rf"(?:LMG(?:\s+agregado)?|LMI(?:\s+específico[^\n]*)?|limite máximo de indenização|limite)"
            rf"\s*:?\s*(?:\n\s*)?{padrao_monetario}"
        ) or buscar(rf"DIRECTORS\s*&\s*OFFICERS\s+{padrao_monetario}")
        if valor is None:
            valor = buscar(rf"importância\s+segurada\s*:\s*{padrao_monetario}")
        limite = converter_moeda(valor)
        cobertura = buscar(r"(?m)^cobertura:\s*(.+)$")
        exclusao = buscar(r"(?m)^exclus(?:ão|ao):\s*(.+)$")
        franquia_valor = buscar(
            rf"(?:franquia|retenção|participação obrigatória)"
            rf"[^\n:]*:?\s*(?:\n\s*)?{padrao_monetario}"
        ) or buscar(rf"franquia\s+ou\s+POS[\s\S]{{0,400}}?{padrao_monetario}")
        franquia = converter_moeda(franquia_valor)
        if franquia is None:
            franquia_zero = buscar(
                r"(?im)^\s*(DIRECTORS\s*&\s*OFFICERS[^\n]*\b(?:zero|sem\s+franquia)\b[^\n]*)$"
            )
            if franquia_zero:
                franquia_valor = franquia_zero
                franquia = Decimal("0")
        numero = (
            buscar(r"(?im)^\s*ap[oó]lice:\s*([A-Z0-9&\-/]+)")
            or buscar(r"(?im)^n[uú]mero da ap[oó]lice\s*:?\s*([A-Z0-9&\-/]{4,})\s*$")
            or buscar(r"\b((?:DNO|D&O|DO)-[A-Z0-9-]{4,})\b")
            or self._extrair_numero_cabecalho(linhas)
        )
        seguradora_cabecalho = self._extrair_seguradora_cabecalho(linhas, numero)
        seguradora = self._limpar_seguradora(
            buscar(r"(?im)^\s*seguradora:\s*(.+)$")
            or buscar(r"(?im)^([^\n]{3,100}(?:seguros|seguradora)\s+s\.?a\.?)\s*$")
            or seguradora_cabecalho
        )
        segurado = (
            buscar(r"(?im)^\s*segurado:\s*(.+)$")
            or buscar(r"(?im)^\s*tomador\s*:?\s*\n\s*([^\n]+)")
            or self._extrair_segurado_cabecalho(linhas)
        )
        inicio_vigencia, fim_vigencia = self._extrair_vigencia(texto, linhas)
        coberturas_tabela = self._extrair_coberturas_tabela(linhas)
        pontos_relevantes = self._extrair_pontos_relevantes(linhas)
        coberturas_relevantes = pontos_relevantes["coberturas"]
        exclusoes_relevantes = pontos_relevantes["exclusoes"]
        clausulas_relevantes = pontos_relevantes["clausulas"]
        apolice = ApoliceEstruturada(
            numero=numero,
            seguradora=seguradora,
            segurado=segurado,
            inicio_vigencia=inicio_vigencia,
            fim_vigencia=fim_vigencia,
            limites=[
                Limite(
                    tipo="LMI",
                    valor=limite,
                    descricao="Limite identificado pela extração local de contingência.",
                    evidencia=Evidencia(texto=valor or "Limite não localizado"),
                )
            ] if limite is not None else [],
            franquias=[
                Franquia(
                    tipo="Franquia principal",
                    valor=franquia,
                    evidencia=Evidencia(texto=franquia_valor or ""),
                )
            ] if franquia is not None else [],
            coberturas=(coberturas_tabela + coberturas_relevantes)
            or (
                [
                    Clausula(
                        categoria="coberturas",
                        titulo="Cobertura identificada",
                        conteudo=cobertura,
                        evidencia=Evidencia(texto=cobertura),
                    )
                ]
                if cobertura
                else []
            ),
            exclusoes=exclusoes_relevantes
            + (
                [
                    Clausula(
                        categoria="exclusoes",
                        titulo="Exclusão identificada",
                        conteudo=exclusao,
                        evidencia=Evidencia(texto=exclusao),
                    )
                ]
                if exclusao
                else []
            ),
            clausulas=clausulas_relevantes,
            aviso=AVISO_REVISAO_HUMANA,
        )
        return RespostaLLMExtracao(
            apolice=apolice,
            confianca=0.35,
            requer_revisao_humana=True,
            justificativa="Extração local de contingência usada porque a resposta da LLM não pôde ser validada.",
        )

    @classmethod
    def _extrair_pontos_relevantes(cls, linhas: list[str]) -> dict[str, list[Clausula]]:
        """Preserva trechos que sustentam os critérios relevantes do seguro D&O."""

        regras = (
            ("clausulas", "Base de reclamações e retroatividade", ("retroatividade", "claims made")),
            ("clausulas", "Prazos adicionais", ("prazos adicionais", "prazo complementar")),
            ("coberturas", "Custos de defesa", ("custos de defesa",)),
            (
                "exclusoes",
                "Exclusões críticas",
                ("principais riscos excluídos", "exclusões", "atos dolosos", "fraude"),
            ),
            ("clausulas", "Âmbito territorial", ("âmbito territorial", "âmbito geográfico")),
            ("coberturas", "Forma de indenização", ("reembolso ao segurado", "reembolso à sociedade")),
            ("coberturas", "Cobertura A - administrador não reembolsado", ("cobertura a",)),
            ("coberturas", "Cobertura B - reembolso à entidade", ("cobertura b",)),
            ("coberturas", "Cobertura C - responsabilidade da entidade", ("cobertura c",)),
            ("coberturas", "Multas e penalidades seguráveis", ("multas ou penalidades",)),
            ("coberturas", "Gerenciamento de crise", ("gerenciamento de crise",)),
            ("coberturas", "Extensões adicionais", ("investigação formal", "indisponibilidade de bens")),
        )
        resultado: dict[str, list[Clausula]] = {
            "coberturas": [],
            "exclusoes": [],
            "clausulas": [],
        }
        linhas_normalizadas = [cls._normalizar_texto(linha) for linha in linhas]
        for categoria, titulo, palavras in regras:
            indice = next(
                (
                    posicao
                    for posicao, linha in enumerate(linhas_normalizadas)
                    if any(cls._normalizar_texto(palavra) in linha for palavra in palavras)
                ),
                None,
            )
            if indice is None:
                continue
            trecho = linhas[indice].strip()
            if len(trecho) < 30:
                trecho = " ".join(linhas[indice : indice + 2]).strip()
            trecho = trecho[:700]
            if not trecho:
                continue
            resultado[categoria].append(
                Clausula(
                    categoria=categoria,
                    titulo=titulo,
                    conteudo=trecho,
                    evidencia=Evidencia(texto=trecho),
                )
            )
        return resultado

    @staticmethod
    def _normalizar_texto(valor: str) -> str:
        """Remove acentos e uniformiza caixa para localizar termos do contrato."""

        decomposicao = unicodedata.normalize("NFKD", valor)
        return "".join(caractere for caractere in decomposicao if not unicodedata.combining(caractere)).casefold()

    @staticmethod
    def _extrair_numero_cabecalho(linhas: list[str]) -> str | None:
        """Lê o número na linha de valores de cabeçalhos tabulares de seguradoras."""

        for indice, linha in enumerate(linhas[:-1]):
            normalizada = linha.casefold()
            if "filial" not in normalizada or "emissora" not in normalizada or "apolice" not in normalizada:
                continue
            candidatos = re.findall(r"\b\d{10,}\b", linhas[indice + 1])
            if candidatos:
                return candidatos[0]
        return None

    @staticmethod
    def _extrair_coberturas_tabela(linhas: list[str]) -> list[Clausula]:
        """Extrai coberturas contratadas de quadros que quebram títulos em várias linhas."""

        coberturas: list[Clausula] = []
        titulos_vistos: set[str] = set()
        inicio_titulo = re.compile(
            r"^(?:Cobertura\s+[ABC](?:\s*[-–].*)?|Multas?\s+(?:civis\s+)?segur[aá]veis|Gerenciamento\s+de\s+crise)$",
            flags=re.IGNORECASE,
        )
        situacao_valida = re.compile(r"^(?:Contratada|Não\s+contratada|Nao\s+contratada)(?:\s+.*)?$")
        complemento_valor = re.compile(r"^(?:R\$\s*)?[0-9][0-9.,]*%?(?:\s+do\s+LMG)?$", flags=re.IGNORECASE)

        for indice, linha in enumerate(linhas):
            if not inicio_titulo.fullmatch(linha):
                continue
            indice_situacao = None
            for candidato in range(indice + 1, min(indice + 4, len(linhas))):
                if situacao_valida.fullmatch(linhas[candidato]):
                    indice_situacao = candidato
                    break
            if indice_situacao is None:
                continue
            titulo = " ".join(linhas[indice:indice_situacao]).strip()
            situacao = linhas[indice_situacao]
            if indice_situacao + 1 < len(linhas) and complemento_valor.fullmatch(linhas[indice_situacao + 1]):
                situacao = f"{situacao} - {linhas[indice_situacao + 1]}"
            chave = titulo.casefold()
            if chave in titulos_vistos:
                continue
            titulos_vistos.add(chave)
            coberturas.append(
                Clausula(
                    categoria="coberturas",
                    titulo=titulo,
                    conteudo=situacao,
                    evidencia=Evidencia(texto=f"{titulo}: {situacao}"),
                )
            )
        return coberturas

    @staticmethod
    def _extrair_segurado_cabecalho(linhas: list[str]) -> str | None:
        """Lê o nome após o bloco de dados do estipulante ou segurado."""

        for indice, linha in enumerate(linhas):
            if not re.search(r"dados\s+do\s+(?:estipulante\s*/\s*)?segurado", linha, flags=re.IGNORECASE):
                continue
            for candidato in linhas[indice + 1 : indice + 5]:
                if re.search(r"\b(?:nome|cpf|cnpj)\b", candidato, flags=re.IGNORECASE):
                    continue
                nome = re.sub(r"\s+\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\s*$", "", candidato).strip()
                if nome:
                    return nome
        return None

    @staticmethod
    def _limpar_seguradora(valor: str | None) -> str | None:
        """Remove códigos e canais de atendimento capturados junto ao nome."""

        if not valor:
            return None
        valor = re.split(r"\s+-\s+\d{4,}\b|\s+Para\s+falar\s+com\b", valor, maxsplit=1, flags=re.IGNORECASE)[0]
        return valor.strip() or None

    @staticmethod
    def _extrair_seguradora_cabecalho(linhas: list[str], numero: str | None) -> str | None:
        """Reconstrói a seguradora quando o cabeçalho separa rótulos e valores."""

        if not numero:
            return None
        try:
            indice_numero = next(indice for indice, linha in enumerate(linhas) if numero in linha)
        except StopIteration:
            return None

        inicio = None
        for indice in range(indice_numero - 1, max(-1, indice_numero - 12), -1):
            if re.fullmatch(r"vig[eê]ncia", linhas[indice], flags=re.IGNORECASE):
                inicio = indice + 1
                break
        if inicio is None or inicio >= indice_numero:
            return None

        valor = " ".join(linhas[inicio:indice_numero])
        valor = re.sub(r"\s*\(seguradora\s+fict[ií]cia\)\s*$", "", valor, flags=re.IGNORECASE)
        return valor.strip() or None

    @staticmethod
    def _extrair_vigencia(texto: str, linhas: list[str]):
        """Extrai início e fim de vigência em formatos textuais e tabulares."""

        explicito = re.search(
            r"in[ií]cio\s+de\s+vig[eê]ncia\s*:\s*(\d{2}/\d{2}/\d{4})"
            r"[\s\S]{0,120}?fim\s+de\s+vig[eê]ncia\s*:\s*(\d{2}/\d{2}/\d{4})",
            texto,
            flags=re.IGNORECASE,
        )
        periodo = explicito
        if periodo is None:
            trecho = "\n".join(linhas[:40])
            periodo = re.search(
                r"\b(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})\b",
                trecho,
                flags=re.IGNORECASE,
            )
        if periodo is None:
            periodo = re.search(
                r"a\s+partir\s+das\s+24h\s+do\s+dia\s+(\d{2}/\d{2}/\d{4})"
                r"\s+at[eé]\s+(?:à|a)s?\s+24\s*horas?\s+do\s+dia\s*(\d{2}/\d{2}/\d{4})",
                texto,
                flags=re.IGNORECASE,
            )
        if periodo is None:
            periodo = re.search(
                r"per[ií]odo\s+de\s+vig[eê]ncia\s*:\s*(\d{2}/\d{2}/\d{4})"
                r"\D{0,5}(\d{2}/\d{2}/\d{4})",
                texto,
                flags=re.IGNORECASE,
            )
        if periodo is None:
            return None, None

        try:
            inicio = datetime.strptime(periodo.group(1), "%d/%m/%Y").date()
            fim = datetime.strptime(periodo.group(2), "%d/%m/%Y").date()
            return inicio, fim
        except ValueError:
            return None, None
