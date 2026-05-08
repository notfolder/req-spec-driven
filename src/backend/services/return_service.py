"""
返却登録サービスモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-REGISTER-RETURN
  設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
  要件概要: 管理者が返却操作で貸出中状態を解除できること。
  設計概要: current_user_login_id を NULL へ更新して貸出可能へ戻す。
  呼び出し先設計ID: DS-CL-RETURN-SERVICE-FT-REGISTER-RETURN
  呼び出し元設計ID: DS-IF-ASSET-RETURN-API-FT-REGISTER-RETURN
"""

from __future__ import annotations

from ..data.sqlite_gateway import SQLiteGateway


class ReturnService:
    """
    備品返却処理を実行する。

    要件トレーサビリティ:
      要件ID: RQ-FT-REGISTER-RETURN
      設計ID: DS-CL-RETURN-SERVICE-FT-REGISTER-RETURN
      要件概要: 返却登録で貸出中備品を貸出可能へ戻す。
      設計概要: 現在利用者が設定済みであることを確認して解除する。
      呼び出し先設計ID: DS-EV-ASSET-STATE-TRANSITION-DT-ASSET-STATE-TRANSITION
      呼び出し元設計ID: DS-IF-ASSET-RETURN-API-FT-REGISTER-RETURN
    """

    def __init__(self, gateway: SQLiteGateway) -> None:
        """
        サービスに SQLite ゲートウェイを注入する。

        要件トレーサビリティ:
          要件ID: RQ-DT-USE-INTERNAL-DB
          設計ID: DS-FN-REGISTER-RETURN-FT-REGISTER-RETURN
          要件概要: 返却状態を内部DBへ永続化する必要がある。
          設計概要: 更新処理で利用する gateway を保持する。
          呼び出し先設計ID: DS-SC-LOCAL-DB-SCHEMA-DT-USE-INTERNAL-DB
          呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
        """
        self.gateway = gateway

    def register_return(self, asset_id: str) -> None:
        """
        備品の現在利用者を解除する。

        要件トレーサビリティ:
          要件ID: RQ-FT-REGISTER-RETURN
          設計ID: DS-FN-REGISTER-RETURN-FT-REGISTER-RETURN
          要件概要: 返却時に貸出中状態を解除し、再貸出可能にする。
          設計概要: 貸出中判定後に current_user_login_id を NULL へ更新する。
          呼び出し先設計ID: DS-SC-ASSET-COLUMNS-DT-ASSET-ATTRIBUTES
          呼び出し元設計ID: DS-IF-ASSET-RETURN-API-FT-REGISTER-RETURN
        """
        asset = self.gateway.fetch_one(
            "SELECT asset_id, current_user_login_id FROM assets WHERE asset_id = ?",
            (asset_id,),
        )
        if asset is None:
            raise ValueError("対象の備品が存在しません")
        if asset["current_user_login_id"] is None:
            raise ValueError("未貸出の備品は返却できません")

        self.gateway.execute(
            "UPDATE assets SET current_user_login_id = NULL WHERE asset_id = ?",
            (asset_id,),
        )
