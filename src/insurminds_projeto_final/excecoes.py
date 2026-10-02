"""Exceções específicas para tratamento funcional do InsurMinds_Projeto_Final."""

from __future__ import annotations


class ErroInsurMinds_Projeto_Final(Exception):
    """Classe base para falhas funcionais conhecidas da aplicação."""


class ErroDocumentoInvalido(ErroInsurMinds_Projeto_Final):
    """Indica arquivo inválido, duplicado, excessivo ou inseguro."""


class ErroExtracaoTexto(ErroInsurMinds_Projeto_Final):
    """Indica falha ao extrair texto nativo ou por OCR."""


class ErroOCR(ErroInsurMinds_Projeto_Final):
    """Indica falha no provedor de OCR configurado."""


class ErroProvedorLLM(ErroInsurMinds_Projeto_Final):
    """Indica falha de comunicação ou configuração do provedor LLM."""


class ErroRespostaLLMInvalida(ErroInsurMinds_Projeto_Final):
    """Indica resposta da LLM fora do schema esperado."""


class ErroValidacaoEstruturacao(ErroInsurMinds_Projeto_Final):
    """Indica dados extraídos insuficientes ou incoerentes."""


class ErroPersistencia(ErroInsurMinds_Projeto_Final):
    """Indica falha transacional de banco de dados."""


class ErroComparacao(ErroInsurMinds_Projeto_Final):
    """Indica falha ao comparar apólices."""


class ErroGeracaoRelatorio(ErroInsurMinds_Projeto_Final):
    """Indica falha ao gerar HTML ou PDF de comparação."""
