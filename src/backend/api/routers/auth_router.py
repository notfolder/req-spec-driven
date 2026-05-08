"""
認証 API ルーターモジュール。

要件トレーサビリティ:
  要件ID: RQ-NF-AUTHENTICATION-ID-PASSWORD
  設計ID: DS-MD-NGINX-API-PATH-FT-UNIFY-ASSET-LEDGER
  要件概要: ログイン API を /api 配下で提供する必要がある。
  設計概要: 認証サービスと認可サービスを連携してログイン結果を返す。
  呼び出し先設計ID: DS-IF-AUTH-LOGIN-API-NF-AUTHENTICATION-ID-PASSWORD
  呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_auth_service, get_authorization_service
from ..schemas import LoginRequest, LoginResponse
from ...services.auth_service import AuthService
from ...services.authorization_service import AuthorizationService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
) -> LoginResponse:
    """
    ログイン認証を実行してロール別表示情報を返す。

    要件トレーサビリティ:
      要件ID: RQ-TS-VERIFY-LOGIN-ROLE-ROUTING
      設計ID: DS-FN-AUTHENTICATE-USER-NF-AUTHENTICATION-ID-PASSWORD
      要件概要: ロールに応じた画面表示制御がログイン直後に機能する必要がある。
      設計概要: 認証成功後に認可判定して can_manage を返却する。
      呼び出し先設計ID: DS-FN-AUTHENTICATE-USER-NF-AUTHENTICATION-ID-PASSWORD, DS-FN-CHECK-ROLE-NF-AUTHORIZATION-BY-ROLE
      呼び出し元設計ID: DS-IF-AUTH-LOGIN-API-NF-AUTHENTICATION-ID-PASSWORD
    """
    try:
        user = auth_service.authenticate_user(request.login_id, request.password)
        permission = authorization_service.check_role(user["role"])
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return LoginResponse(
        login_id=user["login_id"],
        user_name=user["user_name"],
        role=user["role"],
        can_manage=permission["can_manage"],
    )
