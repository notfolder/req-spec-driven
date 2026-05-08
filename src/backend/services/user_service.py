"""
利用者管理サービスモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-MANAGE-USERS
  設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
  要件概要: 管理者が利用者を登録・更新・削除・一覧できること。
  設計概要: users テーブル操作を UserService に集約して API 層へ提供する。
  呼び出し先設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USERS
  呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
"""

from __future__ import annotations

from .auth_service import hash_password
from ..data.sqlite_gateway import SQLiteGateway


class UserService:
    """
    利用者 CRUD を提供するサービス。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-USERS
      設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USERS
      要件概要: 利用者管理を管理者向け機能として提供する。
      設計概要: 一覧、保存、削除、参照を users テーブルに対して実行する。
      呼び出し先設計ID: DS-SC-USER-TABLE-DT-USER-ENTITY
      呼び出し元設計ID: DS-IF-USER-FORM-FT-MANAGE-USERS, DS-CL-CURRENT-BORROWER-PRESENTER-FT-SHOW-CURRENT-BORROWER
    """

    def __init__(self, gateway: SQLiteGateway) -> None:
        """
        サービスに SQLite ゲートウェイを注入する。

        要件トレーサビリティ:
          要件ID: RQ-DT-USE-INTERNAL-DB
          設計ID: DS-FN-LIST-USERS-FT-MANAGE-USERS
          要件概要: 利用者情報は内部DBで一元管理する。
          設計概要: 依存する DB アクセスを gateway 経由に統一する。
          呼び出し先設計ID: DS-SC-LOCAL-DB-SCHEMA-DT-USE-INTERNAL-DB
          呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
        """
        self.gateway = gateway

    def list_users(self) -> list[dict[str, str]]:
        """
        利用者一覧を返す。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-USERS
          設計ID: DS-FN-LIST-USERS-FT-MANAGE-USERS
          要件概要: 利用者一覧を画面に表示できる必要がある。
          設計概要: users テーブルを login_id 順で取得して辞書へ変換する。
          呼び出し先設計ID: DS-SC-USER-TABLE-DT-USER-ENTITY
          呼び出し元設計ID: DS-IF-USER-LIST-API-FT-MANAGE-USERS
        """
        rows = self.gateway.fetch_all(
            "SELECT login_id, user_name, role FROM users ORDER BY login_id"
        )
        return [dict(row) for row in rows]

    def save_user(self, login_id: str, user_name: str, password: str, role: str) -> None:
        """
        利用者を新規登録または更新する。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-USERS
          設計ID: DS-FN-SAVE-USER-FT-MANAGE-USERS
          要件概要: 利用者情報を作成・更新できる必要がある。
          設計概要: 既存判定後に INSERT または UPDATE を実行する。
          呼び出し先設計ID: DS-SC-USER-COLUMNS-DT-USER-ATTRIBUTES
          呼び出し元設計ID: DS-IF-USER-CREATE-API-FT-MANAGE-USERS, DS-IF-USER-UPDATE-API-FT-MANAGE-USERS
        """
        if role not in {"admin", "viewer"}:
            raise ValueError("role は admin または viewer を指定してください")
        if not login_id.strip() or not user_name.strip() or not password.strip():
            raise ValueError("login_id, user_name, password は必須です")

        existing = self.gateway.fetch_one(
            "SELECT login_id FROM users WHERE login_id = ?", (login_id,)
        )
        password_hash = hash_password(password)
        if existing:
            self.gateway.execute(
                "UPDATE users SET user_name = ?, password_hash = ?, role = ? WHERE login_id = ?",
                (user_name, password_hash, role, login_id),
            )
            return
        self.gateway.execute(
            "INSERT INTO users(login_id, user_name, password_hash, role) VALUES (?, ?, ?, ?)",
            (login_id, user_name, password_hash, role),
        )

    def delete_user(self, login_id: str) -> None:
        """
        利用者を削除する。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-USERS
          設計ID: DS-FN-DELETE-USER-FT-MANAGE-USERS
          要件概要: 管理者が不要な利用者を削除できる必要がある。
          設計概要: 貸出中備品の参照を確認したうえで削除を実行する。
          呼び出し先設計ID: DS-SC-ASSET-COLUMNS-DT-ASSET-ATTRIBUTES
          呼び出し元設計ID: DS-IF-USER-DELETE-API-FT-MANAGE-USERS
        """
        in_use = self.gateway.fetch_one(
            "SELECT asset_id FROM assets WHERE current_user_login_id = ?", (login_id,)
        )
        if in_use:
            raise ValueError("貸出中備品が存在するため削除できません")
        self.gateway.execute("DELETE FROM users WHERE login_id = ?", (login_id,))

    def get_user_name(self, login_id: str) -> str | None:
        """
        ログインIDから利用者名を取得する。

        要件トレーサビリティ:
          要件ID: RQ-FT-SHOW-CURRENT-BORROWER
          設計ID: DS-FN-RESOLVE-CURRENT-BORROWER-FT-SHOW-CURRENT-BORROWER
          要件概要: 現在利用者IDに紐づく氏名を表示する必要がある。
          設計概要: users テーブルを参照して user_name を返す。
          呼び出し先設計ID: DS-SC-USER-TABLE-DT-USER-ENTITY
          呼び出し元設計ID: DS-CL-CURRENT-BORROWER-PRESENTER-FT-SHOW-CURRENT-BORROWER
        """
        row = self.gateway.fetch_one(
            "SELECT user_name FROM users WHERE login_id = ?", (login_id,)
        )
        if row is None:
            return None
        return str(row["user_name"])
