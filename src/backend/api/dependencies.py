"""
FastAPI 依存注入定義モジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-UNIFY-ASSET-LEDGER
  設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
  要件概要: API 層から一貫したサービス構成で業務処理を呼び出す。
  設計概要: Gateway と各サービスを組み立てるファクトリ関数を提供する。
  呼び出し先設計ID: DS-CL-ASSET-LEDGER-FACADE-FT-UNIFY-ASSET-LEDGER
  呼び出し元設計ID: DS-MD-NGINX-API-PATH-FT-UNIFY-ASSET-LEDGER
"""

from __future__ import annotations

from ..data.sqlite_gateway import SQLiteGateway
from ..services.asset_availability_query import AssetAvailabilityQuery
from ..services.asset_ledger_facade import AssetLedgerFacade
from ..services.asset_master_service import AssetMasterService
from ..services.auth_service import AuthService
from ..services.authorization_service import AuthorizationService
from ..services.current_borrower_presenter import CurrentBorrowerPresenter
from ..services.lending_service import LendingService
from ..services.return_service import ReturnService
from ..services.user_service import UserService


def get_gateway() -> SQLiteGateway:
    """
    SQLite ゲートウェイを返す。

    要件トレーサビリティ:
      要件ID: RQ-DT-USE-INTERNAL-DB
      設計ID: DS-FN-LIST-ASSETS-FT-MANAGE-ASSET-MASTER
      要件概要: 全サービスが共通の内部DBに接続する必要がある。
      設計概要: data/app.db を利用する SQLiteGateway を返却する。
      呼び出し先設計ID: DS-SC-LOCAL-DB-SCHEMA-DT-USE-INTERNAL-DB
      呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
    """
    return SQLiteGateway("data/app.db")


def get_auth_service() -> AuthService:
    """
    認証サービスを返す。

    要件トレーサビリティ:
      要件ID: RQ-NF-AUTHENTICATION-ID-PASSWORD
      設計ID: DS-FN-AUTHENTICATE-USER-NF-AUTHENTICATION-ID-PASSWORD
      要件概要: ログイン認証を API から利用できる必要がある。
      設計概要: AuthService を生成して返却する。
      呼び出し先設計ID: DS-CL-AUTH-SERVICE-NF-AUTHENTICATION-ID-PASSWORD
      呼び出し元設計ID: DS-IF-AUTH-LOGIN-API-NF-AUTHENTICATION-ID-PASSWORD
    """
    return AuthService(get_gateway())


def get_authorization_service() -> AuthorizationService:
    """
    認可サービスを返す。

    要件トレーサビリティ:
      要件ID: RQ-NF-AUTHORIZATION-BY-ROLE
      設計ID: DS-FN-CHECK-ROLE-NF-AUTHORIZATION-BY-ROLE
      要件概要: ロール別の表示制御を判定する必要がある。
      設計概要: AuthorizationService のインスタンスを返す。
      呼び出し先設計ID: DS-CL-AUTHORIZATION-SERVICE-NF-AUTHORIZATION-BY-ROLE
      呼び出し元設計ID: DS-IF-ROLE-ROUTING-UI-ROLE-BASED-SCREENS
    """
    return AuthorizationService()


def get_user_service() -> UserService:
    """
    利用者サービスを返す。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-USERS
      設計ID: DS-FN-LIST-USERS-FT-MANAGE-USERS
      要件概要: 利用者CRUD機能を API から利用する。
      設計概要: UserService を生成して返却する。
      呼び出し先設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USERS
      呼び出し元設計ID: DS-IF-USER-LIST-API-FT-MANAGE-USERS
    """
    return UserService(get_gateway())


def get_asset_ledger_facade() -> AssetLedgerFacade:
    """
    備品台帳ファサードを返す。

    要件トレーサビリティ:
      要件ID: RQ-FT-UNIFY-ASSET-LEDGER
      設計ID: DS-FN-LIST-ASSETS-FT-MANAGE-ASSET-MASTER
      要件概要: 備品業務を単一窓口で扱う必要がある。
      設計概要: 各サービスを組み合わせて AssetLedgerFacade を生成する。
      呼び出し先設計ID: DS-CL-ASSET-MASTER-SERVICE-FT-MANAGE-ASSET-MASTER, DS-CL-LENDING-SERVICE-FT-REGISTER-LENDING, DS-CL-RETURN-SERVICE-FT-REGISTER-RETURN, DS-CL-ASSET-AVAILABILITY-QUERY-FT-VIEW-ASSET-AVAILABILITY
      呼び出し元設計ID: DS-IF-ASSET-LIST-API-FT-MANAGE-ASSET-MASTER
    """
    gateway = get_gateway()
    user_service = UserService(gateway)
    asset_master_service = AssetMasterService(gateway)
    presenter = CurrentBorrowerPresenter(user_service)
    availability_query = AssetAvailabilityQuery(asset_master_service, presenter)
    lending_service = LendingService(gateway)
    return_service = ReturnService(gateway)
    return AssetLedgerFacade(
        asset_master_service=asset_master_service,
        lending_service=lending_service,
        return_service=return_service,
        availability_query=availability_query,
    )
