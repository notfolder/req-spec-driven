"""
備品関連ユースケース集約モジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-UNIFY-ASSET-LEDGER
  設計ID: DS-MD-ASSET-LEDGER-APP-FT-UNIFY-ASSET-LEDGER
  要件概要: 備品管理業務の入口を単一化し、運用差異をなくす。
  設計概要: 備品 CRUD、貸出、返却、一覧取得を1つの窓口で提供する。
  呼び出し先設計ID: DS-CL-ASSET-LEDGER-FACADE-FT-UNIFY-ASSET-LEDGER
  呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
"""

from __future__ import annotations

from .asset_availability_query import AssetAvailabilityQuery
from .asset_master_service import AssetMasterService
from .lending_service import LendingService
from .return_service import ReturnService


class AssetLedgerFacade:
    """
    備品台帳関連ユースケースを集約する。

    要件トレーサビリティ:
      要件ID: RQ-FT-UNIFY-ASSET-LEDGER
      設計ID: DS-CL-ASSET-LEDGER-FACADE-FT-UNIFY-ASSET-LEDGER
      要件概要: 備品操作の入口を統一し、画面側の分岐を単純化する。
      設計概要: 個別サービスを委譲呼び出しし、API 層へ統一インターフェースを提供する。
      呼び出し先設計ID: DS-CL-ASSET-MASTER-SERVICE-FT-MANAGE-ASSET-MASTER, DS-CL-LENDING-SERVICE-FT-REGISTER-LENDING, DS-CL-RETURN-SERVICE-FT-REGISTER-RETURN, DS-CL-ASSET-AVAILABILITY-QUERY-FT-VIEW-ASSET-AVAILABILITY
      呼び出し元設計ID: DS-IF-ASSET-LIST-API-FT-MANAGE-ASSET-MASTER, DS-IF-ASSET-LEND-API-FT-REGISTER-LENDING
    """

    def __init__(
        self,
        asset_master_service: AssetMasterService,
        lending_service: LendingService,
        return_service: ReturnService,
        availability_query: AssetAvailabilityQuery,
    ) -> None:
        """
        ファサードの依存サービスを注入する。

        要件トレーサビリティ:
          要件ID: RQ-FT-UNIFY-ASSET-LEDGER
          設計ID: DS-FN-LIST-ASSETS-FT-MANAGE-ASSET-MASTER
          要件概要: 単一台帳の各操作を同一入口で扱う必要がある。
          設計概要: 各責務サービスのインスタンスを保持する。
          呼び出し先設計ID: DS-CL-ASSET-MASTER-SERVICE-FT-MANAGE-ASSET-MASTER, DS-CL-LENDING-SERVICE-FT-REGISTER-LENDING, DS-CL-RETURN-SERVICE-FT-REGISTER-RETURN, DS-CL-ASSET-AVAILABILITY-QUERY-FT-VIEW-ASSET-AVAILABILITY
          呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
        """
        self.asset_master_service = asset_master_service
        self.lending_service = lending_service
        self.return_service = return_service
        self.availability_query = availability_query

    def list_assets(self) -> list[dict[str, str]]:
        """
        備品一覧を返す。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-ASSET-MASTER
          設計ID: DS-FN-LIST-ASSETS-FT-MANAGE-ASSET-MASTER
          要件概要: 管理画面で備品一覧を参照できる必要がある。
          設計概要: 一覧取得は表示整形済みの availability_query へ委譲する。
          呼び出し先設計ID: DS-FN-LIST-ASSET-AVAILABILITY-FT-VIEW-ASSET-AVAILABILITY
          呼び出し元設計ID: DS-IF-ASSET-LIST-API-FT-MANAGE-ASSET-MASTER
        """
        return self.availability_query.list_asset_availability()

    def save_asset(self, asset_id: str, asset_name: str) -> None:
        """
        備品を登録または更新する。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-ASSET-MASTER
          設計ID: DS-FN-SAVE-ASSET-FT-MANAGE-ASSET-MASTER
          要件概要: 備品マスタを作成・更新できる必要がある。
          設計概要: 備品保存処理を asset_master_service へ委譲する。
          呼び出し先設計ID: DS-CL-ASSET-MASTER-SERVICE-FT-MANAGE-ASSET-MASTER
          呼び出し元設計ID: DS-IF-ASSET-CREATE-API-FT-MANAGE-ASSET-MASTER, DS-IF-ASSET-UPDATE-API-FT-MANAGE-ASSET-MASTER
        """
        self.asset_master_service.save_asset(asset_id, asset_name)

    def delete_asset(self, asset_id: str) -> None:
        """
        備品を削除する。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-ASSET-MASTER
          設計ID: DS-FN-DELETE-ASSET-FT-MANAGE-ASSET-MASTER
          要件概要: 削除ルールに従って備品を削除できる必要がある。
          設計概要: 削除処理を asset_master_service へ委譲する。
          呼び出し先設計ID: DS-CL-ASSET-MASTER-SERVICE-FT-MANAGE-ASSET-MASTER
          呼び出し元設計ID: DS-IF-ASSET-DELETE-API-FT-MANAGE-ASSET-MASTER
        """
        self.asset_master_service.delete_asset(asset_id)

    def register_lending(self, asset_id: str, login_id: str) -> None:
        """
        貸出登録を実行する。

        要件トレーサビリティ:
          要件ID: RQ-FT-REGISTER-LENDING
          設計ID: DS-FN-REGISTER-LENDING-FT-REGISTER-LENDING
          要件概要: 管理者が貸出登録を実行できる必要がある。
          設計概要: 貸出処理を lending_service へ委譲する。
          呼び出し先設計ID: DS-CL-LENDING-SERVICE-FT-REGISTER-LENDING
          呼び出し元設計ID: DS-IF-ASSET-LEND-API-FT-REGISTER-LENDING
        """
        self.lending_service.register_lending(asset_id, login_id)

    def register_return(self, asset_id: str) -> None:
        """
        返却登録を実行する。

        要件トレーサビリティ:
          要件ID: RQ-FT-REGISTER-RETURN
          設計ID: DS-FN-REGISTER-RETURN-FT-REGISTER-RETURN
          要件概要: 管理者が返却登録を実行できる必要がある。
          設計概要: 返却処理を return_service へ委譲する。
          呼び出し先設計ID: DS-CL-RETURN-SERVICE-FT-REGISTER-RETURN
          呼び出し元設計ID: DS-IF-ASSET-RETURN-API-FT-REGISTER-RETURN
        """
        self.return_service.register_return(asset_id)
