"""
利用者 API ルーターモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-MANAGE-USERS
  設計ID: DS-MD-NGINX-API-PATH-FT-UNIFY-ASSET-LEDGER
  要件概要: 利用者CRUD APIを /api 配下で提供する。
  設計概要: UserService を呼び出す一覧、保存、削除のルートを実装する。
  呼び出し先設計ID: DS-IF-USER-LIST-API-FT-MANAGE-USERS
  呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_user_service
from ..schemas import UserSaveRequest
from ...services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
def list_users(user_service: UserService = Depends(get_user_service)) -> list[dict[str, str]]:
    """
    利用者一覧を返す。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-USERS
      設計ID: DS-FN-LIST-USERS-FT-MANAGE-USERS
      要件概要: 利用者一覧を管理画面で確認できる必要がある。
      設計概要: UserService から一覧を取得して返却する。
      呼び出し先設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USERS
      呼び出し元設計ID: DS-IF-USER-LIST-API-FT-MANAGE-USERS
    """
    return user_service.list_users()


@router.post("")
def create_user(
    request: UserSaveRequest,
    user_service: UserService = Depends(get_user_service),
) -> dict[str, str]:
    """
    利用者を登録する。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-USERS
      設計ID: DS-FN-SAVE-USER-FT-MANAGE-USERS
      要件概要: 新規利用者を作成できる必要がある。
      設計概要: save_user を呼び出し、業務エラーを 400 で返す。
      呼び出し先設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USERS
      呼び出し元設計ID: DS-IF-USER-CREATE-API-FT-MANAGE-USERS
    """
    try:
        user_service.save_user(
            login_id=request.login_id,
            user_name=request.user_name,
            password=request.password,
            role=request.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"result": "created"}


@router.put("/{login_id}")
def update_user(
    login_id: str,
    request: UserSaveRequest,
    user_service: UserService = Depends(get_user_service),
) -> dict[str, str]:
    """
    利用者を更新する。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-USERS
      設計ID: DS-FN-SAVE-USER-FT-MANAGE-USERS
      要件概要: 既存利用者を更新できる必要がある。
      設計概要: URL の login_id を利用して save_user を実行する。
      呼び出し先設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USERS
      呼び出し元設計ID: DS-IF-USER-UPDATE-API-FT-MANAGE-USERS
    """
    try:
        user_service.save_user(
            login_id=login_id,
            user_name=request.user_name,
            password=request.password,
            role=request.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"result": "updated"}


@router.delete("/{login_id}")
def delete_user(
    login_id: str,
    user_service: UserService = Depends(get_user_service),
) -> dict[str, str]:
    """
    利用者を削除する。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-USERS
      設計ID: DS-FN-DELETE-USER-FT-MANAGE-USERS
      要件概要: 参照中でない利用者を削除できる必要がある。
      設計概要: delete_user を呼び出し、業務エラーを 400 で返す。
      呼び出し先設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USERS
      呼び出し元設計ID: DS-IF-USER-DELETE-API-FT-MANAGE-USERS
    """
    try:
        user_service.delete_user(login_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"result": "deleted"}
