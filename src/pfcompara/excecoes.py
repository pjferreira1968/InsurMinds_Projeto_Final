"""Exceções específicas para tratamento funcional do PfCompara."""

from __future__ import annotations


class ErroPfCompara(Exception):
    """Classe base para falhas funcionais conhecidas da aplicação."""


class ErroDocumentoInvalido(ErroPfCompara):
    """Indica arquivo inválido, duplicado, excessivo ou inseguro."""


class ErroExtracaoTexto(ErroPfCompara):
    """Indica falha ao extrair texto nativo ou por OCR."""


class ErroOCR(ErroPfCompara):
    """Indica falha no provedor de OCR configurado."""


class ErroProvedorLLM(ErroPfCompara):
    """Indica falha de comunicação ou configuração do provedor LLM."""


class ErroRespostaLLMInvalida(ErroPfCompara):
    """Indica resposta da LLM fora do schema esperado."""


class ErroValidacaoEstruturacao(ErroPfCompara):
    """Indica dados extraídos insuficientes ou incoerentes."""


class ErroPersistencia(ErroPfCompara):
    """Indica falha transacional de banco de dados."""


class ErroComparacao(ErroPfCompara):
    """Indica falha ao comparar apólices."""


class ErroGeracaoRelatorio(ErroPfCompara):
    """Indica falha ao gerar HTML ou PDF de comparação."""
