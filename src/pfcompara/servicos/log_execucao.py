"""Registro de etapas funcionais exibidas durante operações longas."""

from __future__ import annotations

import logging
from collections.abc import Callable


AtualizadorLog = Callable[[list[str]], None]


class LogExecucao:
    """Acumula mensagens numeradas e as envia para logging e interface."""

    def __init__(self, atualizador: AtualizadorLog | None = None) -> None:
        """Configura o publicador opcional que atualiza a interface."""

        self._atualizador = atualizador
        self._mensagens: list[str] = []
        self._logger = logging.getLogger("pfcompara.execucao")

    @property
    def mensagens(self) -> list[str]:
        """Retorna uma cópia das mensagens registradas."""

        return list(self._mensagens)

    def registrar(self, mensagem: str) -> None:
        """Registra e publica uma etapa com numeração sequencial."""

        linha = f"{len(self._mensagens) + 1:02d} {mensagem}"
        self._mensagens.append(linha)
        self._logger.info(linha)
        if self._atualizador:
            self._atualizador(self.mensagens)
