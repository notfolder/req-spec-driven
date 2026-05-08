"""
ヘルスチェック API ルーターモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-UNIFY-ASSET-LEDGER
  設計ID: DS-MD-NGINX-API-PATH-FT-UNIFY-ASSET-LEDGER
  要件概要: API 基盤が起動し疎通できる状態を確認する必要がある。
  設計概要: /api/health へ正常応答を返す最小ルートを提供する。
  呼び出し先設計ID: なし
  呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """
    ヘルスチェック結果を返す。

    要件トレーサビリティ:
      要件ID: RQ-FT-UNIFY-ASSET-LEDGER
      設計ID: DS-FN-LIST-ASSETS-FT-MANAGE-ASSET-MASTER
      要件概要: API が利用可能な状態であることを確認できる必要がある。
      設計概要: 固定の status=ok を返却する。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-MD-NGINX-API-PATH-FT-UNIFY-ASSET-LEDGER
    """
    return {"status": "ok"}
