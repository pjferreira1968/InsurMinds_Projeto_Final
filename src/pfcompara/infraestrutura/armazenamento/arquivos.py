"""Serviço de armazenamento local seguro para documentos recebidos.

O nome original do usuário nunca é usado como caminho final. O serviço calcula
hash SHA-256, valida extensão e tamanho, e salva o conteúdo em diretório
controlado pela aplicação.
"""

from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path
from uuid import uuid4

from pfcompara.configuracao.constantes import EXTENSOES_PERMITIDAS, MIME_TYPES_PERMITIDOS
from pfcompara.configuracao.settings import Settings
from pfcompara.excecoes import ErroDocumentoInvalido


class ServicoArmazenamentoArquivos:
    """Valida e grava arquivos enviados pelo usuário."""

    def __init__(self, settings: Settings) -> None:
        """Configura e cria o diretório persistente de entrada."""

        self.settings = settings
        self.diretorio_entrada = Path(settings.storage_path) / "entrada"
        self.diretorio_entrada.mkdir(parents=True, exist_ok=True)

    def validar(self, nome_original: str, conteudo: bytes, mime_type: str | None) -> tuple[str, int, str, str]:
        """Valida o arquivo sem gravá-lo e retorna seus metadados seguros."""

        extensao = Path(nome_original).suffix.lower()
        if extensao not in EXTENSOES_PERMITIDAS:
            raise ErroDocumentoInvalido("Formato de arquivo não permitido para o MVP.")
        tamanho = len(conteudo)
        limite = self.settings.max_upload_mb * 1024 * 1024
        if tamanho == 0 or tamanho > limite:
            raise ErroDocumentoInvalido("Arquivo vazio ou acima do tamanho máximo permitido.")
        mime_detectado = mime_type or mimetypes.guess_type(nome_original)[0] or "application/octet-stream"
        if mime_detectado not in MIME_TYPES_PERMITIDOS:
            raise ErroDocumentoInvalido("Tipo MIME incompatível com os formatos aceitos.")
        hash_sha256 = hashlib.sha256(conteudo).hexdigest()
        return hash_sha256, tamanho, mime_detectado, extensao

    def salvar(self, conteudo: bytes, extensao: str) -> str:
        """Grava conteúdo já validado com nome interno aleatório."""

        nome_armazenado = f"{uuid4().hex}{extensao}"
        caminho = self.diretorio_entrada / nome_armazenado
        caminho.write_bytes(conteudo)
        return nome_armazenado

    def validar_e_salvar(self, nome_original: str, conteudo: bytes, mime_type: str | None) -> tuple[str, str, int, str]:
        """Valida extensão, tamanho e MIME type antes de salvar o arquivo.

        Returns:
            Tupla com nome armazenado, hash SHA-256, tamanho em bytes e MIME type.
        """

        hash_sha256, tamanho, mime_detectado, extensao = self.validar(nome_original, conteudo, mime_type)
        nome_armazenado = self.salvar(conteudo, extensao)
        return nome_armazenado, hash_sha256, tamanho, mime_detectado

    def caminho_documento(self, nome_armazenado: str) -> Path:
        """Resolve o caminho interno de um documento previamente armazenado."""

        return self.diretorio_entrada / nome_armazenado

    def excluir(self, nome_armazenado: str) -> None:
        """Remove um documento interno sem aceitar caminhos externos."""

        caminho = self.caminho_documento(Path(nome_armazenado).name)
        if caminho.exists():
            caminho.unlink()

    def excluir_relatorios(self, comparacao_ids: list[int]) -> None:
        """Remove relatórios derivados das comparações excluídas."""

        diretorio = Path(self.settings.storage_path) / "relatorios"
        for comparacao_id in comparacao_ids:
            for extensao in ("html", "pdf"):
                caminho = diretorio / f"comparacao_{comparacao_id}.{extensao}"
                if caminho.exists():
                    caminho.unlink()
