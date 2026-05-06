"""
MockDepartmentClient 単体テスト。

要件トレーサビリティ:
  要件ID: RQ-EX-USE-FIXED-RESPONSE-MOCK, RQ-FT-FETCH-DEPT-BY-LOGIN-ID
  設計ID: DS-TEST-UNIT-MOCK-CLIENT (仮ID)
  要件概要: MockDepartmentClient が departments.json・users.json を正しく読み込み、
            ログインIDによる部署名取得が仕様通り動作することを検証する。
  設計概要: 外部DB不要。JSON ファイルの固定データで全シナリオをカバーする。
  呼び出し先: MockDepartmentClient
  呼び出し元: pytest
"""
import pytest
from mock.mock_department_client import MockDepartmentClient


class TestMockDepartmentClientInit:
    """
    要件トレーサビリティ:
      要件ID: RQ-EX-USE-FIXED-RESPONSE-MOCK
      設計ID: DS-TEST-MOCK-INIT (仮ID)
      要件概要: MockDepartmentClient が JSON ファイルを正常に読み込み初期化できること。
    """

    def test_client_initializes_without_error(self):
        client = MockDepartmentClient()
        assert client is not None

    def test_five_departments_loaded(self):
        client = MockDepartmentClient()
        assert len(client._departments) == 5

    def test_six_users_loaded(self):
        client = MockDepartmentClient()
        assert len(client._users) == 6


class TestFetchDepartmentNameByLoginId:
    """
    要件トレーサビリティ:
      要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID
      設計ID: DS-TEST-MOCK-FETCH-DEPT (仮ID)
      要件概要: ログインIDで部署名を取得できること。不一致は None を返すこと。
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = MockDepartmentClient()

    @pytest.mark.parametrize("login_id,expected", [
        ("U001", "営業部"),
        ("U002", "開発部"),
        ("U003", "人事部"),
        ("U004", "経理部"),
        ("U005", "情報システム部"),
        ("admin", "情報システム部"),
    ])
    def test_known_login_id_returns_correct_department(self, login_id, expected):
        assert self.client.fetch_department_name_by_login_id(login_id) == expected

    def test_unknown_login_id_returns_none(self):
        assert self.client.fetch_department_name_by_login_id("unknown_user") is None

    def test_empty_string_login_id_returns_none(self):
        assert self.client.fetch_department_name_by_login_id("") is None

    def test_return_type_is_str_for_known_user(self):
        result = self.client.fetch_department_name_by_login_id("U001")
        assert isinstance(result, str)

    def test_return_type_is_none_for_unknown_user(self):
        result = self.client.fetch_department_name_by_login_id("does_not_exist")
        assert result is None


class TestDisplayLayerFallback:
    """
    照合失敗時に表示層で「不明」へ変換されることを確認するドキュメントテスト。

    要件トレーサビリティ:
      要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID
      設計ID: DS-TEST-FALLBACK-UNKNOWN (仮ID)
      要件概要: None → 「不明」の変換が上位サービス層の責務であることを示す。
    """

    def test_none_result_converts_to_unknown_in_display_layer(self):
        client = MockDepartmentClient()
        result = client.fetch_department_name_by_login_id("not_registered")
        display_value = result if result is not None else "不明"
        assert display_value == "不明"
