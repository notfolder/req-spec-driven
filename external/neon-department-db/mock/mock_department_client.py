"""
Neon PostgreSQL 部署マスタ モッククライアント（固定レスポンスファイル方式: RQ-EX-USE-FIXED-RESPONSE-MOCK）。

テスト時に department_client.py の関数と同一インターフェースを提供する。
departments.json・users.json を読み込み、全テストシナリオをカバーする。

要件トレーサビリティ:
  要件ID: RQ-EX-FETCH-DEPARTMENT-MASTER, RQ-FT-FETCH-DEPT-BY-LOGIN-ID
  設計ID: DS-CL-MOCK-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER (仮ID)
  要件概要: テスト時に外部DB接続なしで部署情報を返す固定レスポンスモック。
  設計概要: departments.json・users.json を起動時に読み込み、メモリ上で照合して結果を返す。
  呼び出し先: なし
  呼び出し元: テストコード・pytest フィクスチャ
"""
import json
import os
from typing import Optional

_MOCK_DIR = os.path.dirname(__file__)


def _load_departments() -> dict:
    """
    departments.json を読み込み {department_id: department_name} の辞書を返す。

    要件トレーサビリティ:
      要件ID: RQ-EX-FETCH-DEPARTMENT-MASTER
      設計ID: DS-FN-LOAD-DEPTS-EX-FETCH-DEPARTMENT-MASTER (仮ID)
      要件概要: モック用部署データを departments.json から読み込む。
      設計概要: JSON ファイルを読み込み、department_id をキーとした辞書に変換する。
      呼び出し先: なし
      呼び出し元: MockDepartmentClient.__init__
    """
    with open(os.path.join(_MOCK_DIR, "departments.json"), encoding="utf-8") as f:
        return {d["department_id"]: d["department_name"] for d in json.load(f)}


def _load_users() -> dict:
    """
    users.json を読み込み {user_id: department_id} の辞書を返す。

    要件トレーサビリティ:
      要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID
      設計ID: DS-FN-LOAD-USERS-FT-FETCH-DEPT-BY-LOGIN-ID (仮ID)
      要件概要: モック用ユーザーデータを users.json から読み込む。
      設計概要: JSON ファイルを読み込み、user_id をキーとした辞書に変換する。
      呼び出し先: なし
      呼び出し元: MockDepartmentClient.__init__
    """
    with open(os.path.join(_MOCK_DIR, "users.json"), encoding="utf-8") as f:
        return {u["user_id"]: u["department_id"] for u in json.load(f)}


class MockDepartmentClient:
    """
    テスト用モッククライアント。department_client.py と同一インターフェースを提供する。

    要件トレーサビリティ:
      要件ID: RQ-EX-FETCH-DEPARTMENT-MASTER, RQ-FT-FETCH-DEPT-BY-LOGIN-ID
      設計ID: DS-CL-MOCK-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER (仮ID)
      要件概要: 外部DB不要で部署情報を返すモック。全テストシナリオに対応する。
      設計概要: 起動時に JSON ファイルを読み込みメモリ上で保持する。
      呼び出し先: なし
      呼び出し元: テストコード
    """

    def __init__(self):
        """
        要件トレーサビリティ:
          要件ID: RQ-EX-FETCH-DEPARTMENT-MASTER
          設計ID: DS-FN-MOCK-INIT-EX-FETCH-DEPARTMENT-MASTER (仮ID)
          要件概要: departments.json と users.json を読み込んで初期化する。
          設計概要: departments と users の辞書をメモリ上に保持する。
          呼び出し先: _load_departments, _load_users
          呼び出し元: テストコード
        """
        self._departments = _load_departments()
        self._users = _load_users()

    def fetch_department_name_by_login_id(self, login_id: str) -> Optional[str]:
        """
        ログインIDに対応する部署名を返す。一致なしは None を返す。

        要件トレーサビリティ:
          要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID
          設計ID: DS-FN-MOCK-FETCH-DEPT-NAME-FT-FETCH-DEPT-BY-LOGIN-ID (仮ID)
          要件概要: login_id で users.json を照合し department_name を返す。不一致は None。
          設計概要: users 辞書で user_id を検索し、取得した department_id で departments 辞書を引く。
          呼び出し先: なし
          呼び出し元: テストコード
        """
        dept_id = self._users.get(login_id)
        if dept_id is None:
            return None
        return self._departments.get(dept_id)

