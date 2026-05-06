"""
department_client 単体テスト（SQLite インメモリDB使用）。

要件トレーサビリティ:
  要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID, RQ-EX-FETCH-DEPARTMENT-MASTER, RQ-NF-EXTERNAL-DB-TIMEOUT
  設計ID: DS-TEST-UNIT-DEPT-CLIENT (仮ID)
  要件概要: fetch_department_name_by_login_id と get_external_db_engine の動作を検証する。
  設計概要: SQLite インメモリDB で demo_users・demo_departments テーブルを再現し、
            実 DB 接続なしでクエリロジックを検証する。
  呼び出し先: src.department_client
  呼び出し元: pytest
"""
import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool, NullPool

from src.department_client import fetch_department_name_by_login_id, get_external_db_engine


@pytest.fixture(scope="module")
def sqlite_engine():
    """
    要件トレーサビリティ:
      要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID
      設計ID: DS-TEST-FIXTURE-SQLITE (仮ID)
      要件概要: テスト用 SQLite インメモリエンジンに demo スキーマとデータを準備する。
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.connect() as conn:
        conn.execute(text(
            "CREATE TABLE demo_departments ("
            "  department_id VARCHAR PRIMARY KEY,"
            "  department_name VARCHAR NOT NULL"
            ")"
        ))
        conn.execute(text(
            "CREATE TABLE demo_users ("
            "  user_id VARCHAR PRIMARY KEY,"
            "  user_name VARCHAR NOT NULL,"
            "  department_id VARCHAR NOT NULL"
            ")"
        ))
        conn.execute(text(
            "INSERT INTO demo_departments VALUES "
            "('D001','営業部'),('D002','開発部'),('D003','人事部'),"
            "('D004','経理部'),('D005','情報システム部')"
        ))
        conn.execute(text(
            "INSERT INTO demo_users VALUES "
            "('U001','テストユーザー01','D001'),"
            "('U002','テストユーザー02','D002'),"
            "('U003','テストユーザー03','D003'),"
            "('U004','テストユーザー04','D004'),"
            "('U005','テストユーザー05','D005'),"
            "('admin','管理者','D005')"
        ))
        conn.commit()
    return engine


class TestFetchDepartmentNameByLoginId:
    """
    要件トレーサビリティ:
      要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID
      設計ID: DS-TEST-FETCH-DEPT-SQLITE (仮ID)
      要件概要: SQLAlchemy エンジン経由で部署名を正しく取得できること。
    """

    @pytest.mark.parametrize("login_id,expected", [
        ("U001", "営業部"),
        ("U002", "開発部"),
        ("U003", "人事部"),
        ("U004", "経理部"),
        ("U005", "情報システム部"),
        ("admin", "情報システム部"),
    ])
    def test_all_users_return_correct_department(self, sqlite_engine, login_id, expected):
        assert fetch_department_name_by_login_id(sqlite_engine, login_id) == expected

    def test_returns_none_for_unknown_user(self, sqlite_engine):
        assert fetch_department_name_by_login_id(sqlite_engine, "nonexistent") is None

    def test_returns_none_for_empty_string(self, sqlite_engine):
        assert fetch_department_name_by_login_id(sqlite_engine, "") is None

    def test_return_type_is_str_for_known_user(self, sqlite_engine):
        result = fetch_department_name_by_login_id(sqlite_engine, "U001")
        assert isinstance(result, str)


class TestGetExternalDbEngine:
    """
    要件トレーサビリティ:
      要件ID: RQ-EX-FETCH-DEPARTMENT-MASTER, RQ-NF-EXTERNAL-DB-TIMEOUT
      設計ID: DS-TEST-GET-ENGINE (仮ID)
      要件概要: EXTERNAL_DB_URL 未設定時は ValueError を送出し、
               設定時は NullPool エンジンを返すこと。
    """

    def test_raises_value_error_when_env_not_set(self, monkeypatch):
        monkeypatch.delenv("EXTERNAL_DB_URL", raising=False)
        with pytest.raises(ValueError, match="EXTERNAL_DB_URL"):
            get_external_db_engine()

    def test_returns_engine_when_env_set(self, monkeypatch):
        from sqlalchemy.engine import Engine
        monkeypatch.setenv("EXTERNAL_DB_URL", "postgresql://user:pass@localhost/testdb")
        engine = get_external_db_engine()
        assert isinstance(engine, Engine)

    def test_engine_uses_null_pool(self, monkeypatch):
        monkeypatch.setenv("EXTERNAL_DB_URL", "postgresql://user:pass@localhost/testdb")
        engine = get_external_db_engine()
        assert isinstance(engine.pool, NullPool)
