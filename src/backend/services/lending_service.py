"""
貸出登録サービスモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-REGISTER-LENDING
  設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
  要件概要: 管理者が備品を貸出中へ変更できること。
  設計概要: 現在利用者IDを設定して状態を貸出中へ遷移させる。
  呼び出し先設計ID: DS-CL-LENDING-SERVICE-FT-REGISTER-LENDING
  呼び出し元設計ID: DS-IF-ASSET-LEND-API-FT-REGISTER-LENDING
"""

from __future__ import annotations

from ..data.sqlite_gateway import SQLiteGateway


class LendingService:
    """
    備品貸出処理を実行する。

    要件トレーサビリティ:
      要件ID: RQ-FT-REGISTER-LENDING
      設計ID: DS-CL-LENDING-SERVICE-FT-REGISTER-LENDING
      要件概要: 貸出時に現在利用者を記録し、貸出可否判断を正確化する。
      設計概要: 未貸出確認後に current_user_login_id を更新する。
      呼び出し先設計ID: DS-EV-ASSET-STATE-TRANSITION-DT-ASSET-STATE-TRANSITION
      呼び出し元設計ID: DS-IF-ASSET-LEND-API-FT-REGISTER-LENDING
    """

    def __init__(self, gateway: SQLiteGateway) -> None:
        """
        サービスに SQLite ゲートウェイを注入する。

        要件トレーサビリティ:
          要件ID: RQ-DT-USE-INTERNAL-DB
          設計ID: DS-FN-REGISTER-LENDING-FT-REGISTER-LENDING
          要件概要: 貸出状態を内部DBへ永続化する必要がある。
          設計概要: 更新処理で利用する gateway を保持する。
          呼び出し先設計ID: DS-SC-LOCAL-DB-SCHEMA-DT-USE-INTERNAL-DB
          呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
        """
        self.gateway = gateway

    def register_lending(self, asset_id: str, login_id: str) -> None:
        """
        備品に現在利用者を設定する。

        要件トレーサビリティ:
          要件ID: RQ-FT-REGISTER-LENDING
          設計ID: DS-FN-REGISTER-LENDING-FT-REGISTER-LENDING
          要件概要: 貸出登録で貸出可能から貸出中へ遷移させる。
          設計概要: 備品存在と未貸出を検証し、利用者存在確認後に更新する。
          呼び出し先設計ID: DS-SC-ASSET-COLUMNS-DT-ASSET-ATTRIBUTES, DS-SC-USER-TABLE-DT-USER-ENTITY
          呼び出し元設計ID: DS-IF-ASSET-LEND-API-FT-REGISTER-LENDING
        """
        asset = self.gateway.fetch_one(
            "SELECT asset_id, current_user_login_id FROM assets WHERE asset_id = ?",
            (asset_id,),
        )
        if asset is None:
            raise ValueError("対象の備品が存在しません")
        if asset["current_user_login_id"] is not None:
            raise ValueError("既に貸出中です")

        user = self.gateway.fetch_one(
            "SELECT login_id FROM users WHERE login_id = ?", (login_id,)
        )
        if user is None:
            raise ValueError("対象の利用者が存在しません")

        self.gateway.execute(
            "UPDATE assets SET current_user_login_id = ? WHERE asset_id = ?",
            (login_id, asset_id),
        )
