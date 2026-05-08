"""
認可サービスモジュール。

要件トレーサビリティ:
  要件ID: RQ-NF-AUTHORIZATION-BY-ROLE
  設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
  要件概要: 管理者と一般利用者の操作権限を分離する。
  設計概要: ロール値から更新操作可否を判定するサービスを提供する。
  呼び出し先設計ID: DS-CL-AUTHORIZATION-SERVICE-NF-AUTHORIZATION-BY-ROLE
  呼び出し元設計ID: DS-IF-ROLE-ROUTING-UI-ROLE-BASED-SCREENS
"""

from __future__ import annotations


class AuthorizationService:
    """
    ロールベースの表示可否を判定する。

    要件トレーサビリティ:
      要件ID: RQ-NF-AUTHORIZATION-BY-ROLE
      設計ID: DS-CL-AUTHORIZATION-SERVICE-NF-AUTHORIZATION-BY-ROLE
      要件概要: 一般利用者に管理系操作を許可しない。
      設計概要: role が admin の場合のみ can_manage を真にする。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-FN-CHECK-ROLE-NF-AUTHORIZATION-BY-ROLE, DS-IF-ASSET-LIST-API-FT-MANAGE-ASSET-MASTER
    """

    def check_role(self, role: str) -> dict[str, bool]:
        """
        ロールに応じた操作可否フラグを返す。

        要件トレーサビリティ:
          要件ID: RQ-UI-ROLE-BASED-SCREENS
          設計ID: DS-FN-CHECK-ROLE-NF-AUTHORIZATION-BY-ROLE
          要件概要: 管理者のみCRUDボタンを表示し、一般利用者は閲覧のみとする。
          設計概要: role から can_manage を判定して UI へ返却する。
          呼び出し先設計ID: なし
          呼び出し元設計ID: DS-IF-ROLE-ROUTING-UI-ROLE-BASED-SCREENS, DS-IF-ASSET-LIST-API-FT-MANAGE-ASSET-MASTER
        """
        if role not in {"admin", "viewer"}:
            raise ValueError("不正なロールです")
        return {"can_manage": role == "admin"}
