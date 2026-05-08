"""
認証サービスモジュール。

要件トレーサビリティ:
  要件ID: RQ-NF-AUTHENTICATION-ID-PASSWORD
  設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
  要件概要: ログインIDとパスワードで利用者を認証する。
  設計概要: users テーブルのハッシュ値と入力パスワードを照合する。
  呼び出し先設計ID: DS-CL-AUTH-SERVICE-NF-AUTHENTICATION-ID-PASSWORD
  呼び出し元設計ID: DS-IF-AUTH-LOGIN-API-NF-AUTHENTICATION-ID-PASSWORD
"""

from __future__ import annotations

import hashlib

from ..data.sqlite_gateway import SQLiteGateway


def hash_password(password: str) -> str:
    """
    パスワードを PBKDF2-HMAC-SHA256 でハッシュ化する。

    要件トレーサビリティ:
      要件ID: RQ-NF-AUTHENTICATION-ID-PASSWORD
      設計ID: DS-FN-AUTHENTICATE-USER-NF-AUTHENTICATION-ID-PASSWORD
      要件概要: 平文パスワードを保存せず安全に認証を行う。
      設計概要: 固定ソルトを使い PBKDF2 を 100000 回反復して16進文字列を返す。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-FN-SAVE-USER-FT-MANAGE-USERS, DS-FN-AUTHENTICATE-USER-NF-AUTHENTICATION-ID-PASSWORD
    """
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        b"asset-ledger-salt",
        100_000,
    )
    return digest.hex()


class AuthService:
    """
    ログイン認証を提供する。

    要件トレーサビリティ:
      要件ID: RQ-NF-AUTHENTICATION-ID-PASSWORD
      設計ID: DS-CL-AUTH-SERVICE-NF-AUTHENTICATION-ID-PASSWORD
      要件概要: ID/パスワード認証を実施し、利用者を識別する。
      設計概要: login_id に対応する利用者を取得し、ハッシュ照合で認証結果を返す。
      呼び出し先設計ID: DS-SC-USER-TABLE-DT-USER-ENTITY
      呼び出し元設計ID: DS-IF-AUTH-LOGIN-API-NF-AUTHENTICATION-ID-PASSWORD
    """

    def __init__(self, gateway: SQLiteGateway) -> None:
        """
        認証サービスを初期化する。

        要件トレーサビリティ:
          要件ID: RQ-DT-USE-INTERNAL-DB
          設計ID: DS-FN-AUTHENTICATE-USER-NF-AUTHENTICATION-ID-PASSWORD
          要件概要: 認証情報を内部DBから取得する。
          設計概要: 認証時に参照する SQLite ゲートウェイを保持する。
          呼び出し先設計ID: DS-SC-LOCAL-DB-SCHEMA-DT-USE-INTERNAL-DB
          呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
        """
        self.gateway = gateway

    def authenticate_user(self, login_id: str, password: str) -> dict[str, str]:
        """
        ログインIDとパスワードを検証し、利用者情報を返す。

        要件トレーサビリティ:
          要件ID: RQ-NF-AUTHENTICATION-ID-PASSWORD
          設計ID: DS-FN-AUTHENTICATE-USER-NF-AUTHENTICATION-ID-PASSWORD
          要件概要: 誤認証を防止し、正しい利用者だけをログインさせる。
          設計概要: users テーブル参照後、ハッシュ比較で失敗時は例外を送出する。
          呼び出し先設計ID: DS-SC-USER-COLUMNS-DT-USER-ATTRIBUTES
          呼び出し元設計ID: DS-IF-AUTH-LOGIN-API-NF-AUTHENTICATION-ID-PASSWORD
        """
        row = self.gateway.fetch_one(
            "SELECT login_id, user_name, password_hash, role FROM users WHERE login_id = ?",
            (login_id,),
        )
        if row is None:
            raise ValueError("ログインIDまたはパスワードが不正です")
        if hash_password(password) != str(row["password_hash"]):
            raise ValueError("ログインIDまたはパスワードが不正です")
        return {
            "login_id": str(row["login_id"]),
            "user_name": str(row["user_name"]),
            "role": str(row["role"]),
        }
