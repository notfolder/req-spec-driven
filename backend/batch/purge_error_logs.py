"""
エラーログ削除バッチ実行モジュール。

要件トレーサビリティ:
  要件ID: RQ-OP-ERROR-LOG-RETENTION-90D
  設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
  要件概要: エラーログは90日保持し、期限超過分を削除する。
  設計概要: 日次運用で90日超レコードを削除するバッチ処理を提供する。
  呼び出し先設計ID: DS-BT-ERROR-LOG-RETENTION-90D-OP-ERROR-LOG-RETENTION-90D
  呼び出し元設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "app.db"


def purge_expired_rows() -> int:
    """
    90日超過のエラーログを削除する。

    Returns:
      削除件数。

    要件トレーサビリティ:
      要件ID: RQ-OP-ERROR-LOG-RETENTION-90D
      設計ID: DS-FN-RESET-USER-PASSWORD-FT-RESET-USER-PASSWORD
      要件概要: エラーログを90日保持し、超過分を除去する。
      設計概要: しきい日付を算出してerror_logを物理削除する。
      呼び出し先設計ID: DS-BT-ERROR-LOG-RETENTION-90D-OP-ERROR-LOG-RETENTION-90D
      呼び出し元設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
    """

    if not DB_PATH.exists():
        return 0

    threshold = (datetime.utcnow() - timedelta(days=90)).isoformat()
    with sqlite3.connect(DB_PATH) as connection:
        result = connection.execute(
            "DELETE FROM error_log WHERE occurred_at < ?",
            (threshold,),
        )
        connection.commit()
        return int(result.rowcount or 0)


def main() -> None:
    """
    バッチ処理のエントリポイント。

    要件トレーサビリティ:
      要件ID: RQ-OP-ERROR-LOG-RETENTION-90D
      設計ID: DS-FN-RESET-USER-PASSWORD-FT-RESET-USER-PASSWORD
      要件概要: 日次でログ保持方針を適用する。
      設計概要: 削除処理を実行し、件数を標準出力へ出力する。
      呼び出し先設計ID: DS-BT-ERROR-LOG-RETENTION-90D-OP-ERROR-LOG-RETENTION-90D
      呼び出し元設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
    """

    deleted = purge_expired_rows()
    print(f"deleted={deleted}")


if __name__ == "__main__":
    main()
