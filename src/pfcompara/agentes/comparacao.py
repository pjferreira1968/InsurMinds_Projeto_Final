"""Comparação determinística, completa ou relevante, entre apólices D&O."""

from __future__ import annotations

import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path

from pfcompara.dominio.enums import ClassificacaoComparacao, ModoComparacao
from pfcompara.dominio.modelos import ApoliceEstruturada, Clausula, Franquia, Limite
from pfcompara.dominio.schemas_comparacao import ItemComparacao, ResultadoComparacao
from pfcompara.excecoes import ErroComparacao


class AgenteComparacao:
    """Compara dados estruturados com rastreabilidade e filtros configuráveis."""

    def __init__(self, caminho_configuracao: Path | None = None) -> None:
        """Define o arquivo JSON que orienta a comparação relevante."""

        raiz = Path(__file__).resolve().parents[3]
        self.caminho_configuracao = caminho_configuracao or raiz / "config" / "pontos_relevantes.json"

    def comparar(
        self,
        apolice_a_id: int,
        apolice_a: ApoliceEstruturada,
        apolice_b_id: int,
        apolice_b: ApoliceEstruturada,
        modo: ModoComparacao = ModoComparacao.COMPLETA,
        apolice_a_nome: str = "Apólice A",
        apolice_b_nome: str = "Apólice B",
        pontos_relevantes_ids: list[str] | None = None,
    ) -> ResultadoComparacao:
        """Compara os campos disponíveis e aplica o filtro do modo selecionado."""

        if apolice_a_id == apolice_b_id:
            raise ErroComparacao("Selecione duas apólices distintas para comparar.")

        itens: list[ItemComparacao] = []
        itens.extend(self._comparar_identificacao(apolice_a, apolice_b))
        itens.extend(self._comparar_vigencia(apolice_a, apolice_b))
        itens.extend(self._comparar_valores("limites", apolice_a.limites, apolice_b.limites))
        itens.extend(self._comparar_valores("franquias", apolice_a.franquias, apolice_b.franquias))
        itens.extend(self._comparar_clausulas("coberturas", apolice_a.coberturas, apolice_b.coberturas))
        itens.extend(self._comparar_clausulas("exclusoes", apolice_a.exclusoes, apolice_b.exclusoes))
        itens.extend(self._comparar_clausulas("clausulas", apolice_a.clausulas, apolice_b.clausulas))

        pontuacao_a = 0.0
        pontuacao_b = 0.0
        pontos_selecionados: list[str] = []
        if modo == ModoComparacao.RELEVANTE:
            configuracao = self._carregar_configuracao()
            configuracao, pontos_selecionados = self._selecionar_pontos(
                configuracao, pontos_relevantes_ids
            )
            itens = self._filtrar_relevantes(itens, configuracao)
            pontuacao_a, pontuacao_b = self._aplicar_pesos(itens, configuracao)

        divergentes = [
            item for item in itens if item.classificacao != ClassificacaoComparacao.EQUIVALENTE
        ]
        resumo = (
            f"Comparação {modo.value}: {len(itens)} critérios analisados e "
            f"{len(divergentes)} divergências identificadas."
        )
        parecer = self._gerar_parecer(
            modo,
            divergentes,
            pontuacao_a,
            pontuacao_b,
            apolice_a_nome,
            apolice_b_nome,
            len(itens),
        )
        return ResultadoComparacao(
            apolice_a_id=apolice_a_id,
            apolice_b_id=apolice_b_id,
            apolice_a_nome=apolice_a_nome,
            apolice_b_nome=apolice_b_nome,
            modo=modo,
            pontos_relevantes_selecionados=pontos_selecionados,
            itens=itens,
            resumo=resumo,
            pontos_atencao=[item.impacto for item in divergentes[:12]],
            pontuacao_apolice_a=pontuacao_a,
            pontuacao_apolice_b=pontuacao_b,
            parecer=parecer,
        )

    def _comparar_identificacao(
        self, a: ApoliceEstruturada, b: ApoliceEstruturada
    ) -> list[ItemComparacao]:
        """Compara número, seguradora e segurado das duas apólices."""

        itens: list[ItemComparacao] = []
        for campo, rotulo in (
            ("numero", "Número da apólice"),
            ("seguradora", "Seguradora"),
            ("segurado", "Segurado ou tomador"),
        ):
            itens.append(self._item_simples("identificacao", rotulo, getattr(a, campo), getattr(b, campo)))
        return itens

    def _comparar_vigencia(
        self, a: ApoliceEstruturada, b: ApoliceEstruturada
    ) -> list[ItemComparacao]:
        """Compara as datas inicial e final do período de vigência."""

        return [
            self._item_simples("vigencia", "Início de vigência", a.inicio_vigencia, b.inicio_vigencia),
            self._item_simples("vigencia", "Fim de vigência", a.fim_vigencia, b.fim_vigencia),
        ]

    def _item_simples(self, categoria: str, campo: str, valor_a: object, valor_b: object) -> ItemComparacao:
        """Cria um item comparativo para campos escalares ou datas."""

        texto_a = str(valor_a) if valor_a is not None else None
        texto_b = str(valor_b) if valor_b is not None else None
        if texto_a is None and texto_b is None:
            classificacao = ClassificacaoComparacao.INDETERMINADO
            impacto = f"{campo} não foi identificado em nenhuma das apólices."
        elif texto_a is None:
            classificacao = ClassificacaoComparacao.AUSENTE_A
            impacto = f"{campo} não foi identificado na primeira apólice."
        elif texto_b is None:
            classificacao = ClassificacaoComparacao.AUSENTE_B
            impacto = f"{campo} não foi identificado na segunda apólice."
        elif texto_a == texto_b:
            classificacao = ClassificacaoComparacao.EQUIVALENTE
            impacto = f"{campo} equivalente."
        else:
            classificacao = ClassificacaoComparacao.DIFERENTE
            impacto = f"{campo} apresenta diferença entre as apólices."
        return ItemComparacao(
            categoria=categoria,
            campo=campo,
            valor_apolice_a=texto_a,
            valor_apolice_b=texto_b,
            classificacao=classificacao,
            impacto=impacto,
        )

    def _comparar_valores(
        self,
        categoria: str,
        valores_a: list[Limite] | list[Franquia],
        valores_b: list[Limite] | list[Franquia],
    ) -> list[ItemComparacao]:
        """Compara separadamente o valor e a moeda de limites ou franquias."""

        mapa_a = {valor.tipo.casefold(): valor for valor in valores_a}
        mapa_b = {valor.tipo.casefold(): valor for valor in valores_b}
        itens: list[ItemComparacao] = []
        singular = "Limite" if categoria == "limites" else "Franquia ou retenção"
        for chave in sorted(set(mapa_a) | set(mapa_b)):
            valor_a = mapa_a.get(chave)
            valor_b = mapa_b.get(chave)
            numero_a = valor_a.valor if valor_a else None
            numero_b = valor_b.valor if valor_b else None
            moeda_a = valor_a.moeda if valor_a else None
            moeda_b = valor_b.moeda if valor_b else None
            referencia = valor_a or valor_b
            classificacao_valor, impacto_valor = self._classificar_valor_financeiro(
                singular, valor_a, valor_b, numero_a, numero_b
            )
            classificacao_moeda, impacto_moeda = self._classificar_moeda(
                singular, valor_a, valor_b, moeda_a, moeda_b
            )
            evidencia_a = valor_a.evidencia if valor_a else None
            evidencia_b = valor_b.evidencia if valor_b else None
            itens.extend(
                [
                ItemComparacao(
                    categoria=categoria,
                    campo=f"{referencia.tipo} - valor",
                    valor_apolice_a=self._formatar_numero(numero_a),
                    valor_apolice_b=self._formatar_numero(numero_b),
                    classificacao=classificacao_valor,
                    impacto=impacto_valor,
                    evidencia_a=evidencia_a,
                    evidencia_b=evidencia_b,
                ),
                ItemComparacao(
                    categoria=categoria,
                    campo=f"{referencia.tipo} - moeda",
                    valor_apolice_a=moeda_a,
                    valor_apolice_b=moeda_b,
                    classificacao=classificacao_moeda,
                    impacto=impacto_moeda,
                    evidencia_a=evidencia_a,
                    evidencia_b=evidencia_b,
                ),
                ]
            )
        return itens

    def _classificar_valor_financeiro(
        self, singular: str, valor_a, valor_b, numero_a: Decimal | None, numero_b: Decimal | None
    ) -> tuple[ClassificacaoComparacao, str]:
        """Classifica presença e equivalência de um valor financeiro."""

        rotulo = "Valor do limite" if singular == "Limite" else "Valor da franquia ou retenção"
        if valor_a is None or numero_a is None:
            if valor_b is None or numero_b is None:
                return ClassificacaoComparacao.INDETERMINADO, f"{rotulo} não identificado em nenhuma das apólices."
            return ClassificacaoComparacao.AUSENTE_A, f"{rotulo} não identificado na primeira apólice."
        if valor_b is None or numero_b is None:
            return ClassificacaoComparacao.AUSENTE_B, f"{rotulo} não identificado na segunda apólice."
        if self._mesmo_valor(numero_a, numero_b):
            return ClassificacaoComparacao.EQUIVALENTE, f"{rotulo} equivalente."
        return ClassificacaoComparacao.DIFERENTE, f"{rotulo} diferente entre as apólices."

    @staticmethod
    def _classificar_moeda(
        singular: str, valor_a, valor_b, moeda_a: str | None, moeda_b: str | None
    ) -> tuple[ClassificacaoComparacao, str]:
        """Classifica a moeda sem misturá-la à diferença de valor."""

        rotulo = "Moeda do limite" if singular == "Limite" else "Moeda da franquia ou retenção"
        if valor_a is None or not moeda_a:
            if valor_b is None or not moeda_b:
                return ClassificacaoComparacao.INDETERMINADO, f"{rotulo} não identificada em nenhuma das apólices."
            return ClassificacaoComparacao.AUSENTE_A, f"{rotulo} não identificada na primeira apólice."
        if valor_b is None or not moeda_b:
            return ClassificacaoComparacao.AUSENTE_B, f"{rotulo} não identificada na segunda apólice."
        if moeda_a.casefold() == moeda_b.casefold():
            return ClassificacaoComparacao.EQUIVALENTE, f"{rotulo} equivalente ({moeda_a})."
        return ClassificacaoComparacao.DIFERENTE, f"{rotulo} diferente entre as apólices."

    def _comparar_clausulas(
        self, categoria: str, clausulas_a: list[Clausula], clausulas_b: list[Clausula]
    ) -> list[ItemComparacao]:
        """Relaciona cláusulas por título normalizado e compara seu conteúdo."""

        mapa_a = {self._chave_clausula(clausula.titulo): clausula for clausula in clausulas_a}
        mapa_b = {self._chave_clausula(clausula.titulo): clausula for clausula in clausulas_b}
        itens: list[ItemComparacao] = []
        for titulo in sorted(set(mapa_a) | set(mapa_b)):
            clausula_a = mapa_a.get(titulo)
            clausula_b = mapa_b.get(titulo)
            if clausula_a and clausula_b:
                equivalentes = clausula_a.conteudo.strip().casefold() == clausula_b.conteudo.strip().casefold()
                classificacao = (
                    ClassificacaoComparacao.EQUIVALENTE
                    if equivalentes
                    else ClassificacaoComparacao.DIFERENTE
                )
            else:
                classificacao = (
                    ClassificacaoComparacao.AUSENTE_A
                    if clausula_b
                    else ClassificacaoComparacao.AUSENTE_B
                )
            referencia = clausula_a or clausula_b
            itens.append(
                ItemComparacao(
                    categoria=categoria,
                    campo=referencia.titulo,
                    valor_apolice_a=clausula_a.conteudo if clausula_a else None,
                    valor_apolice_b=clausula_b.conteudo if clausula_b else None,
                    classificacao=classificacao,
                    impacto=f"A cláusula de {categoria} requer revisão comparativa.",
                    evidencia_a=clausula_a.evidencia if clausula_a else None,
                    evidencia_b=clausula_b.evidencia if clausula_b else None,
                )
            )
        return itens

    def _carregar_configuracao(self) -> dict:
        """Carrega e valida sintaticamente o arquivo de pontos relevantes."""

        try:
            return json.loads(self.caminho_configuracao.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ErroComparacao(
                f"Não foi possível carregar os pontos relevantes: {self.caminho_configuracao}"
            ) from exc

    def listar_pontos_relevantes(self) -> list[dict]:
        """Retorna cópias dos pontos disponíveis para seleção na interface e API."""

        return [dict(ponto) for ponto in self._carregar_configuracao().get("pontos", [])]

    @staticmethod
    def _selecionar_pontos(
        configuracao: dict, pontos_relevantes_ids: list[str] | None
    ) -> tuple[dict, list[str]]:
        """Valida a seleção e devolve somente os pontos escolhidos pelo usuário."""

        pontos = configuracao.get("pontos", [])
        if not pontos_relevantes_ids:
            raise ErroComparacao("Selecione ao menos um ponto relevante para realizar a comparação.")
        por_id = {ponto.get("id"): ponto for ponto in pontos if ponto.get("id")}
        desconhecidos = sorted(set(pontos_relevantes_ids) - set(por_id))
        if desconhecidos:
            raise ErroComparacao(
                "Pontos relevantes não encontrados na configuração: " + ", ".join(desconhecidos)
            )
        ids_unicos = list(dict.fromkeys(pontos_relevantes_ids))
        selecionados = [por_id[item_id] for item_id in ids_unicos]
        configuracao_filtrada = {**configuracao, "pontos": selecionados}
        rotulos = [
            ponto.get("rotulo") or str(ponto["id"]).replace("_", " ").title()
            for ponto in selecionados
        ]
        return configuracao_filtrada, rotulos

    def _filtrar_relevantes(
        self, itens: list[ItemComparacao], configuracao: dict
    ) -> list[ItemComparacao]:
        """Mantém itens selecionados e explicita critérios não encontrados."""

        pontos = configuracao.get("pontos", [])
        itens_relevantes: list[ItemComparacao] = []
        ids_encontrados: set[str] = set()

        for item in itens:
            criterio = self._criterio_para_item(item, pontos)
            if criterio is None:
                continue
            itens_relevantes.append(item)
            if criterio.get("id"):
                ids_encontrados.add(criterio["id"])

        for ponto in pontos:
            if ponto.get("id") in ids_encontrados:
                continue
            rotulo = ponto.get("rotulo") or str(ponto.get("id", "Ponto relevante")).replace(
                "_", " "
            ).title()
            categorias = ponto.get("categorias", [])
            itens_relevantes.append(
                ItemComparacao(
                    categoria=categorias[0] if categorias else "pontos_relevantes",
                    campo="Critério selecionado",
                    valor_apolice_a="Não encontrado",
                    valor_apolice_b="Não encontrado",
                    classificacao=ClassificacaoComparacao.NAO_ENCONTRADO,
                    impacto=(
                        f'O ponto relevante "{rotulo}" não foi encontrado em nenhuma das apólices.'
                    ),
                    criterio_relevante=rotulo,
                    peso=max(0.0, float(ponto.get("peso", 1))),
                )
            )

        return itens_relevantes

    def _aplicar_pesos(self, itens: list[ItemComparacao], configuracao: dict) -> tuple[float, float]:
        """Associa pesos configuráveis e calcula vantagem apenas quando há direção objetiva."""

        total_a = 0.0
        total_b = 0.0
        for item in itens:
            criterio = self._criterio_para_item(item, configuracao.get("pontos", []))
            if criterio is None:
                continue
            peso = max(0.0, float(criterio.get("peso", 1)))
            item.criterio_relevante = criterio.get("rotulo") or str(
                criterio.get("id", item.campo)
            ).replace("_", " ").title()
            item.peso = peso
            regra = criterio.get("regra_avaliacao", "equivalencia")
            vencedor = self._avaliar_vantagem(item, regra)
            if vencedor == "a":
                item.pontos_apolice_a = peso
                total_a += peso
            elif vencedor == "b":
                item.pontos_apolice_b = peso
                total_b += peso
        return total_a, total_b

    def _criterio_para_item(self, item: ItemComparacao, pontos: list[dict]) -> dict | None:
        """Localiza o critério configurado mais adequado para um item extraído."""

        if item.criterio_relevante:
            rotulo_item = self._normalizar(item.criterio_relevante)
            for ponto in pontos:
                rotulo = ponto.get("rotulo") or str(ponto.get("id", "")).replace("_", " ").title()
                if self._normalizar(rotulo) == rotulo_item:
                    return ponto
        texto = self._normalizar(
            " ".join(filter(None, [item.campo, item.valor_apolice_a, item.valor_apolice_b]))
        )
        correspondentes = []
        for ponto in pontos:
            if item.categoria not in ponto.get("categorias", []):
                continue
            palavras = [self._normalizar(valor) for valor in ponto.get("palavras_chave", [])]
            if not palavras or any(palavra in texto for palavra in palavras):
                correspondentes.append(ponto)
        if not correspondentes:
            return None
        return max(correspondentes, key=lambda ponto: float(ponto.get("peso", 1)))

    def _avaliar_vantagem(self, item: ItemComparacao, regra: str) -> str | None:
        """Aplica a regra de negócio e indica a apólice favorecida, quando mensurável."""

        if item.classificacao == ClassificacaoComparacao.EQUIVALENTE:
            return None
        if regra in {"maior_valor", "menor_valor"}:
            valor_a = self._numero_formatado(item.valor_apolice_a)
            valor_b = self._numero_formatado(item.valor_apolice_b)
            if valor_a is None or valor_b is None or valor_a == valor_b:
                return None
            maior = "a" if valor_a > valor_b else "b"
            return maior if regra == "maior_valor" else ("b" if maior == "a" else "a")
        if regra == "presenca":
            if item.classificacao == ClassificacaoComparacao.AUSENTE_A:
                return "b"
            if item.classificacao == ClassificacaoComparacao.AUSENTE_B:
                return "a"
            estado_a = self._estado_cobertura(item.valor_apolice_a)
            estado_b = self._estado_cobertura(item.valor_apolice_b)
            if estado_a != estado_b and None not in (estado_a, estado_b):
                return "a" if estado_a else "b"
            if estado_a is True and estado_b is True:
                valor_a = self._valor_monetario_texto(item.valor_apolice_a)
                valor_b = self._valor_monetario_texto(item.valor_apolice_b)
                if valor_a is not None and valor_b is not None and valor_a != valor_b:
                    return "a" if valor_a > valor_b else "b"
        return None

    @staticmethod
    def _gerar_parecer(
        modo: ModoComparacao,
        divergentes: list[ItemComparacao],
        pontuacao_a: float,
        pontuacao_b: float,
        nome_a: str,
        nome_b: str,
        total_itens: int,
    ) -> str:
        """Resume equivalência, ausência de dados ou vantagem ponderada."""

        if modo != ModoComparacao.RELEVANTE:
            return "Use o modo Relevante para obter o parecer ponderado."
        if total_itens == 0:
            return "Não foram identificados dados comparáveis para os pontos relevantes selecionados."
        nao_encontrados = [
            item
            for item in divergentes
            if item.classificacao == ClassificacaoComparacao.NAO_ENCONTRADO
        ]
        if len(nao_encontrados) == total_itens:
            return "Os pontos relevantes selecionados não foram encontrados nas apólices comparadas."
        divergencias_identificadas = [
            item
            for item in divergentes
            if item.classificacao != ClassificacaoComparacao.NAO_ENCONTRADO
        ]
        if not divergencias_identificadas and nao_encontrados:
            quantidade = len(nao_encontrados)
            sufixo = "não foi encontrado" if quantidade == 1 else "não foram encontrados"
            return (
                "As apólices são equivalentes nos pontos identificados. "
                f"{quantidade} ponto(s) selecionado(s) {sufixo}."
            )
        if not divergentes:
            return "As apólices são equivalentes nos pontos relevantes identificados."
        if pontuacao_a == pontuacao_b:
            return (
                "As apólices apresentam diferenças, mas a pontuação ponderada não permite "
                "indicar vantagem objetiva para uma delas."
            )
        vencedora = nome_a if pontuacao_a > pontuacao_b else nome_b
        letra = "A" if pontuacao_a > pontuacao_b else "B"
        return (
            f"A Apólice {letra} ({vencedora}) é mais vantajosa nos pontos relevantes "
            f"mensuráveis, com pontuação {max(pontuacao_a, pontuacao_b):g} contra "
            f"{min(pontuacao_a, pontuacao_b):g}."
        )

    @classmethod
    def _chave_clausula(cls, titulo: str) -> str:
        """Produz uma chave estável para relacionar títulos equivalentes."""

        normalizado = cls._normalizar(titulo)
        for chave in ("cobertura a", "cobertura b", "cobertura c"):
            if normalizado.startswith(chave):
                return chave
        if "multa" in normalizado or "penalidade" in normalizado:
            return "multas e penalidades"
        if "gerenciamento de crise" in normalizado or "gestao de crise" in normalizado:
            return "gerenciamento de crise"
        return normalizado

    @staticmethod
    def _normalizar(valor: str) -> str:
        """Remove acentos e diferenças de caixa para comparações textuais."""

        texto = unicodedata.normalize("NFKD", valor.casefold())
        return "".join(caractere for caractere in texto if not unicodedata.combining(caractere))

    @staticmethod
    def _numero_formatado(valor: str | None) -> Decimal | None:
        """Converte um número formatado no padrão brasileiro para Decimal."""

        if not valor:
            return None
        try:
            return Decimal(valor.replace(".", "").replace(",", "."))
        except InvalidOperation:
            return None

    @classmethod
    def _estado_cobertura(cls, valor: str | None) -> bool | None:
        """Infere se o texto informa cobertura contratada, excluída ou indefinida."""

        if not valor:
            return None
        normalizado = cls._normalizar(valor)
        if "nao contratad" in normalizado or "excluid" in normalizado:
            return False
        if "contratad" in normalizado or "incluid" in normalizado or "cobert" in normalizado:
            return True
        return None

    @staticmethod
    def _valor_monetario_texto(valor: str | None) -> Decimal | None:
        """Extrai o primeiro valor em reais presente em um texto de cobertura."""

        if not valor:
            return None
        achado = re.search(r"R\$\s*([0-9][0-9.]*(?:,[0-9]{2})?)", valor)
        if not achado:
            return None
        try:
            return Decimal(achado.group(1).replace(".", "").replace(",", "."))
        except InvalidOperation:
            return None

    @staticmethod
    def _formatar_numero(valor: Decimal | None) -> str | None:
        """Formata Decimal com separadores brasileiros para exibição."""

        if valor is None:
            return None
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def _mesmo_valor(valor_a: Decimal | None, valor_b: Decimal | None) -> bool:
        """Confirma a igualdade quando os dois valores foram identificados."""

        return valor_a is not None and valor_b is not None and valor_a == valor_b
