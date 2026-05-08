"""
API 入出力スキーマ定義モジュール。

要件トレーサビリティ:
  要件ID: RQ-UI-APPLICATION-TYPE-GUI
  設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
  要件概要: GUI 画面が利用する API 入出力を明確に定義する。
  設計概要: FastAPI/Pydantic のモデルで各エンドポイントの契約を固定化する。
  呼び出し先設計ID: なし
  呼び出し元設計ID: DS-IF-AUTH-LOGIN-API-NF-AUTHENTICATION-ID-PASSWORD, DS-IF-ASSET-LIST-API-FT-MANAGE-ASSET-MASTER
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """
    ログイン API リクエスト。

    要件トレーサビリティ:
      要件ID: RQ-NF-AUTHENTICATION-ID-PASSWORD
      設計ID: DS-CL-AUTH-SERVICE-NF-AUTHENTICATION-ID-PASSWORD
      要件概要: ログインIDとパスワードで認証する。
      設計概要: login_id と password の2項目を受け取る。
      呼び出し先設計ID: DS-FN-AUTHENTICATE-USER-NF-AUTHENTICATION-ID-PASSWORD
      呼び出し元設計ID: DS-IF-AUTH-LOGIN-API-NF-AUTHENTICATION-ID-PASSWORD
    """

    login_id: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    """
    ログイン API レスポンス。

    要件トレーサビリティ:
      要件ID: RQ-UI-ROLE-BASED-SCREENS
      設計ID: DS-IF-ROLE-ROUTING-UI-ROLE-BASED-SCREENS
      要件概要: ログイン後にロール別表示制御を行う。
      設計概要: role と can_manage を返却し、画面側で表示を切り替える。
      呼び出し先設計ID: DS-FN-CHECK-ROLE-NF-AUTHORIZATION-BY-ROLE
      呼び出し元設計ID: DS-IF-AUTH-LOGIN-API-NF-AUTHENTICATION-ID-PASSWORD
    """

    login_id: str
    user_name: str
    role: str
    can_manage: bool


class AssetSaveRequest(BaseModel):
    """
    備品保存リクエスト。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-ASSET-MASTER
      設計ID: DS-FN-SAVE-ASSET-FT-MANAGE-ASSET-MASTER
      要件概要: 備品を作成・更新できること。
      設計概要: asset_id と asset_name を受け取って保存処理へ渡す。
      呼び出し先設計ID: DS-CL-ASSET-MASTER-SERVICE-FT-MANAGE-ASSET-MASTER
      呼び出し元設計ID: DS-IF-ASSET-CREATE-API-FT-MANAGE-ASSET-MASTER, DS-IF-ASSET-UPDATE-API-FT-MANAGE-ASSET-MASTER
    """

    asset_id: str = Field(min_length=1)
    asset_name: str = Field(min_length=1)


class LendingRequest(BaseModel):
    """
    貸出登録リクエスト。

    要件トレーサビリティ:
      要件ID: RQ-FT-REGISTER-LENDING
      設計ID: DS-FN-REGISTER-LENDING-FT-REGISTER-LENDING
      要件概要: 貸出時に利用者IDを指定して登録する。
      設計概要: login_id を受け取り貸出処理へ渡す。
      呼び出し先設計ID: DS-CL-LENDING-SERVICE-FT-REGISTER-LENDING
      呼び出し元設計ID: DS-IF-ASSET-LEND-API-FT-REGISTER-LENDING
    """

    login_id: str = Field(min_length=1)


class UserSaveRequest(BaseModel):
    """
    利用者保存リクエスト。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-USERS
      設計ID: DS-FN-SAVE-USER-FT-MANAGE-USERS
      要件概要: 利用者の登録・更新ができること。
      設計概要: login_id、user_name、password、role を受け取る。
      呼び出し先設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USERS
      呼び出し元設計ID: DS-IF-USER-CREATE-API-FT-MANAGE-USERS, DS-IF-USER-UPDATE-API-FT-MANAGE-USERS
    """

    login_id: str = Field(min_length=1)
    user_name: str = Field(min_length=1)
    password: str = Field(min_length=1)
    role: str = Field(min_length=1)
