"""アプリ設定を環境変数から読み込む。

要件トレーサビリティ:
  要件ID: RQ-OP-INITIAL-ADMIN-ENV
  設計ID: DS-MD-BACKEND-CONFIG-OP-INITIAL-ADMIN-ENV
  要件概要: 初回起動時に環境変数から初期管理者情報を使う。
  設計概要: 必須環境変数を読み込み、未設定時に起動失敗させる。
  呼び出し先: なし
  呼び出し元: DS-MD-BACKEND-APP-FT-MANAGE-EQUIPMENT
"""
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """設定値コンテナ。

    要件トレーサビリティ:
      要件ID: RQ-OP-INITIAL-ADMIN-ENV
      設計ID: DS-MD-BACKEND-CONFIG-OP-INITIAL-ADMIN-ENV
      要件概要: 初期管理者ログインIDとパスワードとDBパスを設定する。
      設計概要: バックエンドが参照する実行時設定を不変データで保持する。
      呼び出し先: なし
      呼び出し元: DS-MD-BACKEND-APP-FT-MANAGE-EQUIPMENT
    """

    admin_login_id: str
    admin_password: str
    db_path: str


def _required(key: str) -> str:
    """必須環境変数を取得する。"""
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"必須環境変数が未設定です: {key}")
    return value


def load_settings() -> Settings:
    """環境変数から設定を読み込む。"""
    return Settings(
        admin_login_id=_required("INITIAL_ADMIN_LOGIN_ID"),
        admin_password=_required("INITIAL_ADMIN_PASSWORD"),
        db_path=_required("APP_DB_PATH"),
    )
