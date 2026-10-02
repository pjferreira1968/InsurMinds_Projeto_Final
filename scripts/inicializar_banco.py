"""Inicializa o banco configurado para o InsurMinds_Projeto_Final.

O script pode ser executado diretamente a partir da raiz do projeto e funciona
com o SQLite padrão ou com a opção PostgreSQL definida em ``DATABASE_URL``.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
SRC = RAIZ_PROJETO / "src"


def _preparar_importacao(database_url: str | None) -> None:
    """Configura o diretório e o caminho de importação antes de carregar a aplicação."""

    os.chdir(RAIZ_PROJETO)
    sys.path.insert(0, str(SRC))
    if database_url:
        os.environ["DATABASE_URL"] = database_url


def _criar_diretorio_sqlite(database_url: str) -> None:
    """Cria o diretório pai do arquivo SQLite quando a URL usar caminho relativo."""

    from sqlalchemy.engine import make_url

    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        return

    caminho_banco = Path(url.database)
    if not caminho_banco.is_absolute():
        caminho_banco = RAIZ_PROJETO / caminho_banco
    caminho_banco.parent.mkdir(parents=True, exist_ok=True)


def inicializar(database_url: str | None, aguardar_segundos: int) -> int:
    """Testa a conexão, cria as tabelas ausentes e informa o resultado."""

    _preparar_importacao(database_url)

    from sqlalchemy import inspect, text
    from sqlalchemy.engine import make_url
    from sqlalchemy.exc import SQLAlchemyError

    from insurminds_projeto_final.configuracao.settings import obter_settings
    from insurminds_projeto_final.infraestrutura.banco.conexao import criar_tabelas, engine

    settings = obter_settings()
    _criar_diretorio_sqlite(settings.database_url)
    url_segura = make_url(settings.database_url).render_as_string(hide_password=True)
    limite = time.monotonic() + aguardar_segundos

    print(f"Banco configurado: {url_segura}")
    while True:
        try:
            with engine.connect() as conexao:
                conexao.execute(text("SELECT 1"))
            criar_tabelas()
            tabelas = ", ".join(sorted(inspect(engine).get_table_names()))
            print(f"Banco inicializado com sucesso. Tabelas disponíveis: {tabelas}")
            return 0
        except SQLAlchemyError as erro:
            if time.monotonic() >= limite:
                print(
                    "Não foi possível conectar ou inicializar o banco. "
                    "Confirme DATABASE_URL, credenciais, porta e disponibilidade do serviço."
                )
                print(f"Detalhe técnico: {erro}")
                return 1
            time.sleep(2)


def main() -> int:
    """Interpreta os argumentos e executa a inicialização do banco."""

    parser = argparse.ArgumentParser(description="Inicializa o banco do InsurMinds_Projeto_Final.")
    parser.add_argument(
        "--database-url",
        help="Sobrescreve DATABASE_URL somente nesta execução.",
    )
    parser.add_argument(
        "--aguardar-segundos",
        type=int,
        default=30,
        help="Tempo máximo para aguardar o banco ficar disponível (padrão: 30).",
    )
    argumentos = parser.parse_args()
    return inicializar(argumentos.database_url, max(0, argumentos.aguardar_segundos))


if __name__ == "__main__":
    raise SystemExit(main())
