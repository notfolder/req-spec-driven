"""
SQLite 接続と SQL 実行を担うデータアクセスモジュール。

要件トレーサビリティ:
  要件ID: RQ-DT-USE-INTERNAL-DB
  設計ID: DS-SC-LOCAL-DB-SCHEMA-DT-USE-INTERNAL-DB
  要件概要: 単一台帳を安定運用するため、内部DBを利用してデータを永続化する。
  設計概要: SQLite ファイル接続、初期テーブル作成、共通 CRUD 実行を提供する。
  呼び出し先設計ID: なし
  呼び出し元設計ID: DS-CL-ASSET-MASTER-SERVICE-FT-MANAGE-ASSET-MASTER, DS-CL-USER-SERVICE-FT-MANAGE-USERS
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class SQLiteGateway:
    """
    SQLite への接続とクエリ実行を集約する。

    要件トレーサビリティ:
      要件ID: RQ-DT-NO-EXTERNAL-DB-CONNECTION
      設計ID: DS-CL-ASSET-MASTER-SERVICE-FT-MANAGE-ASSET-MASTER
      要件概要: 外部DBへ接続せず、ローカルDBのみを利用する。
      設計概要: DB ファイルパスを固定し、同一接続方式で各サービスへ提供する。
      呼び出し先設計ID: DS-SC-LOCAL-DB-SCHEMA-DT-USE-INTERNAL-DB
      呼び出し元設計ID: DS-CL-AUTH-SERVICE-NF-AUTHENTICATION-ID-PASSWORD, DS-CL-USER-SERVICE-FT-MANAGE-USERS
    """

    def __init__(self, db_path: str = "data/app.db") -> None:
        """
        SQLite ゲートウェイを初期化する。

        要件トレーサビリティ:
          要件ID: RQ-DT-USE-INTERNAL-DB
          設計ID: DS-FN-LIST-ASSETS-FT-MANAGE-ASSET-MASTER
          要件概要: 内部DBの初期化をアプリ起動時に実施する必要がある。
          設計概要: DB ファイルへのパスを保持し、接続作成時に利用する。
          呼び出し先設計ID: DS-SC-LOCAL-DB-SCHEMA-DT-USE-INTERNAL-DB
          呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """
        Row 形式で参照可能な SQLite 接続を返す。

        要件トレーサビリティ:
          要件ID: RQ-DT-USE-INTERNAL-DB
          設計ID: DS-FN-GET-ASSET-DETAIL-FT-MANAGE-ASSET-MASTER
          要件概要: 台帳データを取得するためにDB接続が必要である。
          設計概要: row_factory を sqlite3.Row に設定した接続を返す。
          呼び出し先設計ID: なし
          呼び出し元設計ID: DS-CL-ASSET-MASTER-SERVICE-FT-MANAGE-ASSET-MASTER, DS-CL-USER-SERVICE-FT-MANAGE-USERS
        """
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize_schema(self) -> None:
        """
        users と assets テーブルを作成する。

        要件トレーサビリティ:
          要件ID: RQ-DT-USER-ENTITY
          設計ID: DS-FN-SAVE-USER-FT-MANAGE-USERS
          要件概要: 利用者エンティティと備品エンティティを内部DBで管理する。
          設計概要: 起動時に CREATE TABLE IF NOT EXISTS を実行して初期化する。
          呼び出し先設計ID: DS-SC-USER-TABLE-DT-USER-ENTITY, DS-SC-ASSET-TABLE-DT-ASSET-ENTITY
          呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
        """
        with self.get_connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    login_id TEXT PRIMARY KEY,
                    user_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role in ('admin', 'viewer'))
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS assets (
                    asset_id TEXT PRIMARY KEY,
                    asset_name TEXT NOT NULL,
                    current_user_login_id TEXT NULL,
                    FOREIGN KEY(current_user_login_id) REFERENCES users(login_id)
                )
                """
            )
            connection.commit()

    def fetch_all(self, query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        """
        複数行取得クエリを実行して結果一覧を返す。

        要件トレーサビリティ:
          要件ID: RQ-FT-VIEW-ASSET-AVAILABILITY
          設計ID: DS-FN-LIST-ASSET-AVAILABILITY-FT-VIEW-ASSET-AVAILABILITY
          要件概要: 備品一覧の貸出状態を一覧取得できる必要がある。
          設計概要: SELECT クエリを実行して結果行を配列で返却する。
          呼び出し先設計ID: なし
          呼び出し元設計ID: DS-CL-ASSET-AVAILABILITY-QUERY-FT-VIEW-ASSET-AVAILABILITY, DS-CL-USER-SERVICE-FT-MANAGE-USERS
        """
        with self.get_connection() as connection:
            cursor = connection.execute(query, params)
            return cursor.fetchall()

    def fetch_one(self, query: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        """
        単一行取得クエリを実行して結果を返す。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-ASSET-MASTER
          設計ID: DS-FN-GET-ASSET-DETAIL-FT-MANAGE-ASSET-MASTER
          要件概要: 備品詳細を取得して編集や削除判定に利用する。
          設計概要: SELECT 結果の先頭1件を返し、未存在時は None を返す。
          呼び出し先設計ID: なし
          呼び出し元設計ID: DS-CL-ASSET-MASTER-SERVICE-FT-MANAGE-ASSET-MASTER, DS-CL-AUTH-SERVICE-NF-AUTHENTICATION-ID-PASSWORD
        """
        with self.get_connection() as connection:
            cursor = connection.execute(query, params)
            return cursor.fetchone()

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        """
        更新系クエリを実行してコミットする。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-ASSET-MASTER
          設計ID: DS-FN-SAVE-ASSET-FT-MANAGE-ASSET-MASTER
          要件概要: 備品と利用者の登録更新削除を永続化する必要がある。
          設計概要: INSERT/UPDATE/DELETE をトランザクションで実行する。
          呼び出し先設計ID: なし
          呼び出し元設計ID: DS-CL-ASSET-MASTER-SERVICE-FT-MANAGE-ASSET-MASTER, DS-CL-USER-SERVICE-FT-MANAGE-USERS, DS-CL-LENDING-SERVICE-FT-REGISTER-LENDING, DS-CL-RETURN-SERVICE-FT-REGISTER-RETURN
        """
        with self.get_connection() as connection:
            connection.execute(query, params)
            connection.commit()
