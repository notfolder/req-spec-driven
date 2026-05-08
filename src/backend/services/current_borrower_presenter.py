"""
現在利用者表示整形モジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-SHOW-CURRENT-BORROWER
  設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
  要件概要: 備品ごとに現在利用者を一覧で表示できること。
  設計概要: 利用者IDから氏名を解決し、状態文字列を付与する。
  呼び出し先設計ID: DS-CL-CURRENT-BORROWER-PRESENTER-FT-SHOW-CURRENT-BORROWER
  呼び出し元設計ID: DS-CL-ASSET-AVAILABILITY-QUERY-FT-VIEW-ASSET-AVAILABILITY
"""

from __future__ import annotations

from .user_service import UserService


class CurrentBorrowerPresenter:
    """
    現在利用者表示情報を生成する。

    要件トレーサビリティ:
      要件ID: RQ-FT-SHOW-CURRENT-BORROWER
      設計ID: DS-CL-CURRENT-BORROWER-PRESENTER-FT-SHOW-CURRENT-BORROWER
      要件概要: 現在利用者と貸出状態を即時把握できる表示が必要である。
      設計概要: current_user_login_id から user_name と状態ラベルを構築する。
      呼び出し先設計ID: DS-FN-RESOLVE-CURRENT-BORROWER-FT-SHOW-CURRENT-BORROWER
      呼び出し元設計ID: DS-FN-LIST-ASSET-AVAILABILITY-FT-VIEW-ASSET-AVAILABILITY
    """

    def __init__(self, user_service: UserService) -> None:
        """
        利用者サービスを注入する。

        要件トレーサビリティ:
          要件ID: RQ-FT-SHOW-CURRENT-BORROWER
          設計ID: DS-FN-RESOLVE-CURRENT-BORROWER-FT-SHOW-CURRENT-BORROWER
          要件概要: 利用者名の解決には利用者マスタ参照が必要である。
          設計概要: UserService を保持して氏名取得へ利用する。
          呼び出し先設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USERS
          呼び出し元設計ID: DS-CL-ASSET-AVAILABILITY-QUERY-FT-VIEW-ASSET-AVAILABILITY
        """
        self.user_service = user_service

    def resolve_current_borrower(
        self,
        asset_id: str,
        current_user_login_id: str | None,
    ) -> dict[str, str]:
        """
        現在利用者名と状態表示を返す。

        要件トレーサビリティ:
          要件ID: RQ-FT-SHOW-CURRENT-BORROWER
          設計ID: DS-FN-RESOLVE-CURRENT-BORROWER-FT-SHOW-CURRENT-BORROWER
          要件概要: 一覧に現在利用者または空欄を表示する必要がある。
          設計概要: 利用者IDが無い場合は貸出可能、ある場合は貸出中として氏名を解決する。
          呼び出し先設計ID: DS-FN-LIST-USERS-FT-MANAGE-USERS
          呼び出し元設計ID: DS-FN-LIST-ASSET-AVAILABILITY-FT-VIEW-ASSET-AVAILABILITY
        """
        if current_user_login_id is None:
            return {
                "asset_id": asset_id,
                "status": "貸出可能",
                "current_user_name": "",
            }

        user_name = self.user_service.get_user_name(current_user_login_id)
        if user_name is None:
            raise ValueError("現在利用者IDに対応する利用者が存在しません")

        return {
            "asset_id": asset_id,
            "status": "貸出中",
            "current_user_name": user_name,
        }
