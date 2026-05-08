"""
アプリケーションのログ設定モジュール。

要件トレーサビリティ:
  要件ID: RQ-OP-APPLICATION-LOG-RETENTION
  設計ID: DS-IF-APPLICATION-LOG-OP-APPLICATION-LOG-RETENTION
  要件概要: アプリ動作ログとエラーログを1年間保持し、障害時の原因調査を可能にする。
  設計概要: backend 側で共通のロガー初期化を行い、ファイル出力と標準出力を同時に有効化する。
  呼び出し先設計ID: なし
  呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging() -> None:
    """
    アプリ全体で共通利用するロガーを初期化する。

    要件トレーサビリティ:
      要件ID: RQ-OP-APPLICATION-LOG-RETENTION
      設計ID: DS-FN-AUTHENTICATE-USER-NF-AUTHENTICATION-ID-PASSWORD
      要件概要: 運用で参照可能なログを継続保存できることが必要である。
      設計概要: logs 配下へローテーション付きファイル出力を設定し、コンソールにも同時出力する。
      呼び出し先設計ID: DS-IF-APPLICATION-LOG-OP-APPLICATION-LOG-RETENTION
      呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
    """
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=1_000_000,
        backupCount=12,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(console_handler)
