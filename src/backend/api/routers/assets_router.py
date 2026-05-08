"""
備品 API ルーターモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-MANAGE-ASSET-MASTER
  設計ID: DS-MD-NGINX-API-PATH-FT-UNIFY-ASSET-LEDGER
  要件概要: 備品一覧、CRUD、貸出返却 API を /api 配下で提供する。
  設計概要: AssetLedgerFacade を利用して備品業務を統一的に処理する。
  呼び出し先設計ID: DS-IF-ASSET-LIST-API-FT-MANAGE-ASSET-MASTER
  呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_asset_ledger_facade
from ..schemas import AssetSaveRequest, LendingRequest
from ...services.asset_ledger_facade import AssetLedgerFacade

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.get("")
def list_assets(facade: AssetLedgerFacade = Depends(get_asset_ledger_facade)) -> list[dict[str, str]]:
    """
    備品一覧を返す。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-ASSET-MASTER
      設計ID: DS-FN-LIST-ASSETS-FT-MANAGE-ASSET-MASTER
      要件概要: 管理者画面で備品台帳一覧を参照する必要がある。
      設計概要: ファサード経由で一覧を取得し、そのまま返却する。
      呼び出し先設計ID: DS-CL-ASSET-LEDGER-FACADE-FT-UNIFY-ASSET-LEDGER
      呼び出し元設計ID: DS-IF-ASSET-LIST-API-FT-MANAGE-ASSET-MASTER
    """
    return facade.list_assets()


@router.get("/availability")
def list_asset_availability(
    facade: AssetLedgerFacade = Depends(get_asset_ledger_facade),
) -> list[dict[str, str]]:
    """
    一般利用者向けの貸出可能状態一覧を返す。

    要件トレーサビリティ:
      要件ID: RQ-FT-VIEW-ASSET-AVAILABILITY
      設計ID: DS-FN-LIST-ASSET-AVAILABILITY-FT-VIEW-ASSET-AVAILABILITY
      要件概要: 一般利用者が貸出可能/貸出中を確認できる必要がある。
      設計概要: 同一一覧データを返し、画面側で表示制御を行う。
      呼び出し先設計ID: DS-CL-ASSET-LEDGER-FACADE-FT-UNIFY-ASSET-LEDGER
      呼び出し元設計ID: DS-IF-ASSET-AVAILABILITY-API-FT-VIEW-ASSET-AVAILABILITY
    """
    return facade.list_assets()


@router.post("")
def create_asset(
    request: AssetSaveRequest,
    facade: AssetLedgerFacade = Depends(get_asset_ledger_facade),
) -> dict[str, str]:
    """
    備品を登録する。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-ASSET-MASTER
      設計ID: DS-FN-SAVE-ASSET-FT-MANAGE-ASSET-MASTER
      要件概要: 管理者が備品を新規登録できる必要がある。
      設計概要: save_asset を呼び出して登録結果を返却する。
      呼び出し先設計ID: DS-CL-ASSET-LEDGER-FACADE-FT-UNIFY-ASSET-LEDGER
      呼び出し元設計ID: DS-IF-ASSET-CREATE-API-FT-MANAGE-ASSET-MASTER
    """
    try:
        facade.save_asset(request.asset_id, request.asset_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"result": "created"}


@router.put("/{asset_id}")
def update_asset(
    asset_id: str,
    request: AssetSaveRequest,
    facade: AssetLedgerFacade = Depends(get_asset_ledger_facade),
) -> dict[str, str]:
    """
    備品を更新する。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-ASSET-MASTER
      設計ID: DS-FN-SAVE-ASSET-FT-MANAGE-ASSET-MASTER
      要件概要: 管理者が備品情報を更新できる必要がある。
      設計概要: URL の asset_id を優先して save_asset を呼び出す。
      呼び出し先設計ID: DS-CL-ASSET-LEDGER-FACADE-FT-UNIFY-ASSET-LEDGER
      呼び出し元設計ID: DS-IF-ASSET-UPDATE-API-FT-MANAGE-ASSET-MASTER
    """
    try:
        facade.save_asset(asset_id, request.asset_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"result": "updated"}


@router.delete("/{asset_id}")
def delete_asset(
    asset_id: str,
    facade: AssetLedgerFacade = Depends(get_asset_ledger_facade),
) -> dict[str, str]:
    """
    備品を削除する。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-ASSET-MASTER
      設計ID: DS-FN-DELETE-ASSET-FT-MANAGE-ASSET-MASTER
      要件概要: 貸出中でない備品のみ削除できる必要がある。
      設計概要: ファサードへ削除処理を委譲し、業務エラー時は 400 を返す。
      呼び出し先設計ID: DS-CL-ASSET-LEDGER-FACADE-FT-UNIFY-ASSET-LEDGER
      呼び出し元設計ID: DS-IF-ASSET-DELETE-API-FT-MANAGE-ASSET-MASTER
    """
    try:
        facade.delete_asset(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"result": "deleted"}


@router.post("/{asset_id}/lend")
def register_lending(
    asset_id: str,
    request: LendingRequest,
    facade: AssetLedgerFacade = Depends(get_asset_ledger_facade),
) -> dict[str, str]:
    """
    貸出登録を実行する。

    要件トレーサビリティ:
      要件ID: RQ-FT-REGISTER-LENDING
      設計ID: DS-FN-REGISTER-LENDING-FT-REGISTER-LENDING
      要件概要: 管理者が利用者を指定して貸出登録できる必要がある。
      設計概要: register_lending を呼び出して結果を返却する。
      呼び出し先設計ID: DS-CL-ASSET-LEDGER-FACADE-FT-UNIFY-ASSET-LEDGER
      呼び出し元設計ID: DS-IF-ASSET-LEND-API-FT-REGISTER-LENDING
    """
    try:
        facade.register_lending(asset_id, request.login_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"result": "lended"}


@router.post("/{asset_id}/return")
def register_return(
    asset_id: str,
    facade: AssetLedgerFacade = Depends(get_asset_ledger_facade),
) -> dict[str, str]:
    """
    返却登録を実行する。

    要件トレーサビリティ:
      要件ID: RQ-FT-REGISTER-RETURN
      設計ID: DS-FN-REGISTER-RETURN-FT-REGISTER-RETURN
      要件概要: 管理者が返却登録を実行できる必要がある。
      設計概要: register_return を呼び出して結果を返却する。
      呼び出し先設計ID: DS-CL-ASSET-LEDGER-FACADE-FT-UNIFY-ASSET-LEDGER
      呼び出し元設計ID: DS-IF-ASSET-RETURN-API-FT-REGISTER-RETURN
    """
    try:
        facade.register_return(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"result": "returned"}
