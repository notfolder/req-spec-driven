"""
備品貸出可能状態一覧取得モジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-VIEW-ASSET-AVAILABILITY
  設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
  要件概要: 一般利用者が貸出可能/貸出中を一覧で確認できること。
  設計概要: 備品一覧を取得し、現在利用者表示を整形して返却する。
  呼び出し先設計ID: DS-CL-ASSET-AVAILABILITY-QUERY-FT-VIEW-ASSET-AVAILABILITY
  呼び出し元設計ID: DS-IF-ASSET-AVAILABILITY-API-FT-VIEW-ASSET-AVAILABILITY
"""

from __future__ import annotations

from .asset_master_service import AssetMasterService
from .current_borrower_presenter import CurrentBorrowerPresenter


class AssetAvailabilityQuery:
    """
    備品一覧を表示向け形式へ変換して返す。

    要件トレーサビリティ:
      要件ID: RQ-FT-VIEW-ASSET-AVAILABILITY
      設計ID: DS-CL-ASSET-AVAILABILITY-QUERY-FT-VIEW-ASSET-AVAILABILITY
      要件概要: 全備品の貸出状態を一覧表示する必要がある。
      設計概要: AssetMasterService で台帳を取得し、Presenter で表示値を補完する。
      呼び出し先設計ID: DS-FN-LIST-ASSET-AVAILABILITY-FT-VIEW-ASSET-AVAILABILITY
      呼び出し元設計ID: DS-IF-ASSET-AVAILABILITY-API-FT-VIEW-ASSET-AVAILABILITY
    """

    def __init__(
        self,
        asset_master_service: AssetMasterService,
        current_borrower_presenter: CurrentBorrowerPresenter,
    ) -> None:
        """
        必要な依存サービスを注入する。

        要件トレーサビリティ:
          要件ID: RQ-FT-UNIFY-ASSET-LEDGER
          設計ID: DS-FN-LIST-ASSET-AVAILABILITY-FT-VIEW-ASSET-AVAILABILITY
          要件概要: 単一台帳を共通サービスから参照する必要がある。
          設計概要: 台帳参照と表示整形の責務を別サービスに分離して構成する。
          呼び出し先設計ID: DS-CL-ASSET-MASTER-SERVICE-FT-MANAGE-ASSET-MASTER, DS-CL-CURRENT-BORROWER-PRESENTER-FT-SHOW-CURRENT-BORROWER
          呼び出し元設計ID: DS-CL-ASSET-LEDGER-FACADE-FT-UNIFY-ASSET-LEDGER
        """
        self.asset_master_service = asset_master_service
        self.current_borrower_presenter = current_borrower_presenter

    def list_asset_availability(self) -> list[dict[str, str]]:
        """
        備品一覧へ貸出状態と現在利用者名を付与して返す。

        要件トレーサビリティ:
          要件ID: RQ-FT-VIEW-ASSET-AVAILABILITY
          設計ID: DS-FN-LIST-ASSET-AVAILABILITY-FT-VIEW-ASSET-AVAILABILITY
          要件概要: 備品一覧で貸出可能状態を確認できる必要がある。
          設計概要: 各備品について Presenter を呼び出し、表示辞書の配列を返す。
          呼び出し先設計ID: DS-FN-LIST-ASSETS-FT-MANAGE-ASSET-MASTER, DS-FN-RESOLVE-CURRENT-BORROWER-FT-SHOW-CURRENT-BORROWER
          呼び出し元設計ID: DS-IF-ASSET-AVAILABILITY-API-FT-VIEW-ASSET-AVAILABILITY, DS-IF-ASSET-LIST-API-FT-MANAGE-ASSET-MASTER
        """
        assets = self.asset_master_service.list_assets()
        results: list[dict[str, str]] = []
        for asset in assets:
            resolved = self.current_borrower_presenter.resolve_current_borrower(
                str(asset["asset_id"]),
                None if asset["current_user_login_id"] is None else str(asset["current_user_login_id"]),
            )
            results.append(
                {
                    "asset_id": str(asset["asset_id"]),
                    "asset_name": str(asset["asset_name"]),
                    "status": resolved["status"],
                    "current_user_name": resolved["current_user_name"],
                }
            )
        return results
