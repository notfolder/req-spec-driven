"""E2Eシナリオテスト。"""
import os
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

os.environ["INITIAL_ADMIN_LOGIN_ID"] = "admin"
os.environ["INITIAL_ADMIN_PASSWORD"] = "adminpass"
os.environ["APP_DB_PATH"] = "/tmp/equipment_loan_e2e.db"

from backend.app.main import app  # noqa: E402


def _client() -> TestClient:
    """テストクライアントを作成する。"""
    return TestClient(app)


def _login(client: TestClient, login_id: str, password: str) -> str:
    """ログインしてトークンを返す。"""
    res = client.post("/api/auth/login", json={"login_id": login_id, "password": password})
    assert res.status_code == 200
    return res.json()["token"]


def test_full_flow():
    """管理者・一般利用者・備品貸出返却のE2Eを検証する。"""
    client = _client()
    client.get("/api/health")
    admin_token = _login(client, "admin", "adminpass")

    create_user = client.post("/api/users", headers={"x-session-token": admin_token}, json={"display_name": "一般", "login_id": "general", "password": "generalpass", "role": "general"})
    assert create_user.status_code == 200
    general_id = create_user.json()["id"]

    create_equipment = client.post("/api/equipment", headers={"x-session-token": admin_token}, json={"equipment_code": "E001", "name": "ノートPC"})
    assert create_equipment.status_code == 200
    equipment = create_equipment.json()

    loan = client.post("/api/loans", headers={"x-session-token": admin_token}, json={"equipment_id": equipment["id"], "user_id": general_id, "loan_date": "2026-05-06", "version": equipment["version"]})
    assert loan.status_code == 200

    me_general_token = _login(client, "general", "generalpass")
    eq_list_for_general = client.get("/api/equipment", headers={"x-session-token": me_general_token})
    assert eq_list_for_general.status_code == 200
    assert eq_list_for_general.json()[0]["status"] == "loaned"

    returned = client.post("/api/returns", headers={"x-session-token": admin_token}, json={"equipment_id": equipment["id"], "version": loan.json()["version"]})
    assert returned.status_code == 200
    assert returned.json()["status"] == "available"

    logout = client.post("/api/auth/logout", headers={"x-session-token": admin_token})
    assert logout.status_code == 200


def test_auto_logout():
    """60分超過で自動ログアウトされることを検証する。"""
    client = _client()
    client.get("/api/health")
    admin_token = _login(client, "admin", "adminpass")

    from backend.app.main import session_factory
    from backend.app.models import SessionModel

    db = session_factory()
    try:
        session = db.get(SessionModel, admin_token)
        session.expires_at = datetime.utcnow() - timedelta(minutes=1)
        db.commit()
    finally:
        db.close()

    res = client.get("/api/auth/me", headers={"x-session-token": admin_token})
    assert res.status_code == 401
