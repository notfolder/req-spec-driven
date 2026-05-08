"""
備品マスタ管理サービスモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-MANAGE-ASSET-MASTER
  設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
  要件概要: 備品の登録、更新、削除、一覧、詳細を管理する。
  設計概要: assets テーブルへの CRUD と削除時の貸出中チェックを提供する。
  呼び出し先設計ID: DS-CL-ASSET-MASTER-SERVICE-FT-MANAGE-ASSET-MASTER
  呼び出し元設計ID: DS-CL-ASSET-LEDGER-FACADE-FT-UNIFY-ASSET-LEDGER
"""

from __future__ import annotations

from ..data.sqlite_gateway import SQLiteGateway


class AssetMasterService:
    """
    備品台帳の CRUD を提供する。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-ASSET-MASTER
      設計ID: DS-CL-ASSET-MASTER-SERVICE-FT-MANAGE-ASSET-MASTER
      要件概要: 単一台帳として備品情報を管理できる必要がある。
      設計概要: assets テーブルに対する一覧、詳細、保存、削除を実装する。
      呼び出し先設計ID: DS-SC-ASSET-TABLE-DT-ASSET-ENTITY
      呼び出し元設計ID: DS-IF-ASSET-LIST-API-FT-MANAGE-ASSET-MASTER, DS-IF-ASSET-DELETE-API-FT-MANAGE-ASSET-MASTER
    """

    def __init__(self, gateway: SQLiteGateway) -> None:
        """
        サービスに SQLite ゲートウェイを注入する。

        要件トレーサビリティ:
          要件ID: RQ-DT-USE-INTERNAL-DB
          設計ID: DS-FN-LIST-ASSETS-FT-MANAGE-ASSET-MASTER
          要件概要: 備品管理は内部DB上で行う必要がある。
          設計概要: 共通 gateway を保持してクエリ実行する。
          呼び出し先設計ID: DS-SC-LOCAL-DB-SCHEMA-DT-USE-INTERNAL-DB
          呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
        """
        self.gateway = gateway

    def list_assets(self) -> list[dict[str, str | None]]:
        """
        備品一覧を返す。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-ASSET-MASTER
          設計ID: DS-FN-LIST-ASSETS-FT-MANAGE-ASSET-MASTER
          要件概要: 備品台帳の全件を確認できる必要がある。
          設計概要: assets を asset_id 順に取得して辞書へ変換する。
          呼び出し先設計ID: DS-SC-ASSET-COLUMNS-DT-ASSET-ATTRIBUTES
          呼び出し元設計ID: DS-IF-ASSET-LIST-API-FT-MANAGE-ASSET-MASTER, DS-FN-LIST-ASSET-AVAILABILITY-FT-VIEW-ASSET-AVAILABILITY
        """
        rows = self.gateway.fetch_all(
            "SELECT asset_id, asset_name, current_user_login_id FROM assets ORDER BY asset_id"
        )
        return [dict(row) for row in rows]

    def get_asset_detail(self, asset_id: str) -> dict[str, str | None]:
        """
        指定備品の詳細情報を返す。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-ASSET-MASTER
          設計ID: DS-FN-GET-ASSET-DETAIL-FT-MANAGE-ASSET-MASTER
          要件概要: 編集・削除時に対象備品の情報を取得する必要がある。
          設計概要: assets テーブルを asset_id で参照し、未存在時は例外を送出する。
          呼び出し先設計ID: DS-SC-ASSET-TABLE-DT-ASSET-ENTITY
          呼び出し元設計ID: DS-IF-ASSET-UPDATE-API-FT-MANAGE-ASSET-MASTER, DS-IF-ASSET-DELETE-API-FT-MANAGE-ASSET-MASTER
        """
        row = self.gateway.fetch_one(
            "SELECT asset_id, asset_name, current_user_login_id FROM assets WHERE asset_id = ?",
            (asset_id,),
        )
        if row is None:
            raise ValueError("対象の備品が存在しません")
        return dict(row)

    def save_asset(self, asset_id: str, asset_name: str) -> None:
        """
        備品を新規登録または更新する。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-ASSET-MASTER
          設計ID: DS-FN-SAVE-ASSET-FT-MANAGE-ASSET-MASTER
          要件概要: 備品の作成と更新を業務で実行できる必要がある。
          設計概要: 既存判定後に INSERT か UPDATE を実行する。
          呼び出し先設計ID: DS-SC-ASSET-COLUMNS-DT-ASSET-ATTRIBUTES
          呼び出し元設計ID: DS-IF-ASSET-CREATE-API-FT-MANAGE-ASSET-MASTER, DS-IF-ASSET-UPDATE-API-FT-MANAGE-ASSET-MASTER
        """
        if not asset_id.strip() or not asset_name.strip():
            raise ValueError("asset_id と asset_name は必須です")
        existing = self.gateway.fetch_one(
            "SELECT asset_id FROM assets WHERE asset_id = ?", (asset_id,)
        )
        if existing:
            self.gateway.execute(
                "UPDATE assets SET asset_name = ? WHERE asset_id = ?",
                (asset_name, asset_id),
            )
            return
        self.gateway.execute(
            "INSERT INTO assets(asset_id, asset_name, current_user_login_id) VALUES (?, ?, NULL)",
            (asset_id, asset_name),
        )

    def delete_asset(self, asset_id: str) -> None:
        """
        貸出中でない備品を削除する。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-ASSET-MASTER
          設計ID: DS-FN-DELETE-ASSET-FT-MANAGE-ASSET-MASTER
          要件概要: 不要備品を削除できるが、貸出中備品の削除は禁止する。
          設計概要: current_user_login_id が NULL の場合のみ DELETE を許可する。
          呼び出し先設計ID: DS-EV-ASSET-STATE-TRANSITION-DT-ASSET-STATE-TRANSITION
          呼び出し元設計ID: DS-IF-ASSET-DELETE-API-FT-MANAGE-ASSET-MASTER
        """
        asset = self.get_asset_detail(asset_id)
        if asset["current_user_login_id"] is not None:
            raise ValueError("貸出中の備品は削除できません")
        self.gateway.execute("DELETE FROM assets WHERE asset_id = ?", (asset_id,))
