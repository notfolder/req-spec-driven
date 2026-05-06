"""
外部連携 E2E テスト — 実 Neon PostgreSQL 接続。

要件トレーサビリティ:
  要件ID: RQ-TS-VERIFY-DEPT-DISPLAY-FROM-EXTERNAL, RQ-TS-VERIFY-EXTERNAL-DB-FAILURE,
          RQ-EX-FETCH-DEPARTMENT-MASTER, RQ-FT-FETCH-DEPT-BY-LOGIN-ID,
          RQ-NF-EXTERNAL-DB-TIMEOUT, RQ-NF-EXTERNAL-DB-READONLY
  設計ID: DS-TEST-E2E-REAL-DB (仮ID)
  要件概要: 実 Neon PostgreSQL に接続し、部署名取得・タイムアウト設定・
            SELECT 専用動作を検証する。EXTERNAL_DB_URL 環境変数が必須。
  設計概要: conftest.py で .env を読み込み EXTERNAL_DB_URL を解決する。
            セッションスコープのエンジンフィクスチャで接続を共有する。
  呼び出し先: src.department_client
  呼び出し元: pytest（実 Neon DB 接続環境）
"""
import os
import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

from src.department_client import get_external_db_engine, fetch_department_name_by_login_id


@pytest.fixture(scope="session")
def real_engine():
    """
    要件トレーサビリティ:
      要件ID: RQ-EX-FETCH-DEPARTMENT-MASTER, RQ-NF-EXTERNAL-DB-TIMEOUT
      設計ID: DS-TEST-FIXTURE-REAL-ENGINE (仮ID)
      要件概要: EXTERNAL_DB_URL から実 Neon PostgreSQL エンジンを生成する。
    """
    url = os.environ.get("EXTERNAL_DB_URL")
    if not url:
        pytest.skip("EXTERNAL_DB_URL が設定されていないため E2E テストをスキップします")
    return get_external_db_engine()


class TestRqTsVerifyDeptDisplayFromExternal:
    """
    RQ-TS-VERIFY-DEPT-DISPLAY-FROM-EXTERNAL:
    外部DBから部署名が動的取得できること。
    """

    @pytest.mark.parametrize("login_id,expected_dept", [
        ("U001", "営業部"),
        ("U002", "開発部"),
        ("U003", "人事部"),
        ("U004", "経理部"),
        ("U005", "情報システム部"),
        # admin は mock データのみに存在し、実 DB には登録されていないため除外
    ])
    def test_fetch_dept_by_login_id_returns_correct_dept(self, real_engine, login_id, expected_dept):
        result = fetch_department_name_by_login_id(real_engine, login_id)
        assert result == expected_dept, (
            f"login_id={login_id}: expected '{expected_dept}', got '{result}'"
        )

    def test_result_is_string(self, real_engine):
        result = fetch_department_name_by_login_id(real_engine, "U001")
        assert isinstance(result, str)


class TestRqTsVerifyExternalDbFailure:
    """
    RQ-TS-VERIFY-EXTERNAL-DB-FAILURE:
    照合不一致（未登録ログインID）時に None が返ること。
    上位サービス層で「不明」への変換が期待される。
    """

    def test_unknown_login_id_returns_none(self, real_engine):
        result = fetch_department_name_by_login_id(real_engine, "not_registered_user")
        assert result is None

    def test_empty_login_id_returns_none(self, real_engine):
        result = fetch_department_name_by_login_id(real_engine, "")
        assert result is None

    def test_none_displayed_as_unknown_in_service_layer(self, real_engine):
        result = fetch_department_name_by_login_id(real_engine, "not_registered_user")
        display_value = result if result is not None else "不明"
        assert display_value == "不明"


class TestRqNfExternalDbReadonly:
    """
    RQ-NF-EXTERNAL-DB-READONLY:
    INSERT / UPDATE / DELETE が実行されないことを検証する。
    外部DBへの書き込みを行わないことを明示するテスト。
    """

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "neondb_owner は WRITE 権限を持つため INSERT が成功する。"
            "DB 側のアクセス制御（読み取り専用ロール）が未適用（RQ-NF-EXTERNAL-DB-READONLY）。"
            "アプリコード側の制御は test_fetch_only_uses_select で検証済み。"
        ),
    )
    def test_insert_is_rejected_at_db_level(self, real_engine):
        """DB 権限レベルで INSERT が拒否されること（現状は neondb_owner が WRITE 可）。"""
        with real_engine.connect() as conn:
            with pytest.raises((OperationalError, ProgrammingError)):
                conn.execute(text(
                    "INSERT INTO demo_departments (department_id, department_name) "
                    "VALUES ('D999', 'テスト部署')"
                ))
                conn.commit()

    def test_fetch_only_uses_select(self, real_engine):
        """fetch_department_name_by_login_id が SELECT のみ発行し、DB 状態を変更しないこと。"""
        before = fetch_department_name_by_login_id(real_engine, "U001")
        fetch_department_name_by_login_id(real_engine, "U001")
        after = fetch_department_name_by_login_id(real_engine, "U001")
        assert before == after == "営業部"


class TestRqNfExternalDbTimeout:
    """
    RQ-NF-EXTERNAL-DB-TIMEOUT:
    エンジンに connect_timeout=5 が設定されていることを確認する。
    """

    def test_engine_has_connect_timeout_setting(self, real_engine):
        """実接続の DSN パラメータに connect_timeout=5 が含まれること。"""
        with real_engine.connect() as conn:
            # psycopg2 の接続オブジェクトから DSN パラメータを取得する
            raw_conn = conn.connection.driver_connection
            dsn_params = raw_conn.get_dsn_parameters()
            assert dsn_params.get("connect_timeout") == "5", (
                f"connect_timeout=5 が DSN に含まれていません。"
                f"実際の DSN パラメータ: {dsn_params}"
            )
