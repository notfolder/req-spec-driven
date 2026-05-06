"""FastAPIエントリーポイント。"""
from datetime import datetime, timedelta
import secrets
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import load_settings
from .db import create_session_factory, db_session_dependency, init_db
from .models import Equipment, SessionModel, User
from .schemas import (
    CreateEquipmentRequest,
    CreateUserRequest,
    EquipmentOut,
    LoanRequest,
    LoginRequest,
    ReturnRequest,
    UpdateEquipmentRequest,
    UpdateUserRequest,
    UserOut,
    VersionRequest,
)
from .security import hash_password, verify_password

settings = load_settings()
session_factory = create_session_factory(settings.db_path)
init_db(session_factory)
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def get_db():
    """DBセッション依存関係を提供する。"""
    yield from db_session_dependency(session_factory)


def _ensure_initial_admin(db: Session) -> None:
    """初回起動時のみ初期管理者を作成する。"""
    if db.query(User).count() == 0:
        db.add(User(display_name="初期管理者", login_id=settings.admin_login_id, password_hash=hash_password(settings.admin_password), role="admin", version=1))
        db.commit()


def _get_session_user(db: Session, token: str | None) -> User:
    """セッションを検証してログイン利用者を返す。"""
    if not token:
        raise HTTPException(status_code=401, detail="未ログインです")
    session = db.get(SessionModel, token)
    if session is None:
        raise HTTPException(status_code=401, detail="未ログインです")
    now = datetime.utcnow()
    if session.expires_at < now:
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=401, detail="セッション期限切れです")
    session.last_accessed_at = now
    session.expires_at = now + timedelta(minutes=60)
    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="利用者が存在しません")
    return user


def _require_admin(user: User) -> None:
    """管理者権限を検証する。"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    """ヘルスチェックと初期管理者の存在保証を行う。"""
    _ensure_initial_admin(db)
    return {"ok": True}


@app.post("/api/auth/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """ログインを実行してセッショントークンを返す。"""
    _ensure_initial_admin(db)
    user = db.query(User).filter(User.login_id == body.login_id).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="ログインIDまたはパスワードが不正です")
    now = datetime.utcnow()
    token = secrets.token_hex(16)
    db.add(SessionModel(id=token, user_id=user.id, last_accessed_at=now, expires_at=now + timedelta(minutes=60)))
    return {"token": token, "user": UserOut.model_validate(user, from_attributes=True).model_dump()}


@app.post("/api/auth/logout")
def logout(x_session_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    """ログアウトしてセッションを削除する。"""
    session = db.get(SessionModel, x_session_token) if x_session_token else None
    if session:
        db.delete(session)
    return {"ok": True}


@app.get("/api/auth/me")
def me(x_session_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    """現在ログイン中の利用者情報を返す。"""
    user = _get_session_user(db, x_session_token)
    return UserOut.model_validate(user, from_attributes=True)


@app.get("/api/equipment")
def list_equipment(x_session_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    """備品一覧を返す。"""
    _get_session_user(db, x_session_token)
    return [EquipmentOut.model_validate(row, from_attributes=True) for row in db.query(Equipment).order_by(Equipment.id).all()]


@app.post("/api/equipment")
def create_equipment(body: CreateEquipmentRequest, x_session_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    """備品を登録する。"""
    user = _get_session_user(db, x_session_token)
    _require_admin(user)
    exists = db.query(Equipment).filter(Equipment.equipment_code == body.equipment_code).first()
    if exists:
        raise HTTPException(status_code=409, detail="備品IDが重複しています")
    row = Equipment(equipment_code=body.equipment_code, name=body.name, status="available", version=1)
    db.add(row)
    db.flush()
    return EquipmentOut.model_validate(row, from_attributes=True)


@app.put("/api/equipment/{equipment_id}")
def update_equipment(equipment_id: int, body: UpdateEquipmentRequest, x_session_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    """備品を更新する。"""
    user = _get_session_user(db, x_session_token)
    _require_admin(user)
    row = db.get(Equipment, equipment_id)
    if row is None:
        raise HTTPException(status_code=404, detail="備品が存在しません")
    if row.version != body.version:
        raise HTTPException(status_code=409, detail="更新競合です")
    row.equipment_code = body.equipment_code
    row.name = body.name
    row.version += 1
    return EquipmentOut.model_validate(row, from_attributes=True)


@app.delete("/api/equipment/{equipment_id}")
def delete_equipment(equipment_id: int, body: VersionRequest, x_session_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    """備品を削除する。"""
    user = _get_session_user(db, x_session_token)
    _require_admin(user)
    row = db.get(Equipment, equipment_id)
    if row is None:
        raise HTTPException(status_code=404, detail="備品が存在しません")
    if row.version != body.version:
        raise HTTPException(status_code=409, detail="更新競合です")
    if row.status != "available":
        raise HTTPException(status_code=400, detail="貸出中の備品は削除できません")
    db.delete(row)
    return {"ok": True}


@app.get("/api/users")
def list_users(x_session_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    """利用者一覧を返す。"""
    user = _get_session_user(db, x_session_token)
    _require_admin(user)
    return [UserOut.model_validate(row, from_attributes=True) for row in db.query(User).order_by(User.id).all()]


@app.post("/api/users")
def create_user(body: CreateUserRequest, x_session_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    """利用者を登録する。"""
    user = _get_session_user(db, x_session_token)
    _require_admin(user)
    exists = db.query(User).filter(User.login_id == body.login_id).first()
    if exists:
        raise HTTPException(status_code=409, detail="ログインIDが重複しています")
    row = User(display_name=body.display_name, login_id=body.login_id, password_hash=hash_password(body.password), role=body.role, version=1)
    db.add(row)
    db.flush()
    return UserOut.model_validate(row, from_attributes=True)


@app.put("/api/users/{user_id}")
def update_user(user_id: int, body: UpdateUserRequest, x_session_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    """利用者情報を更新する。"""
    login_user = _get_session_user(db, x_session_token)
    _require_admin(login_user)
    row = db.get(User, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="利用者が存在しません")
    if row.version != body.version:
        raise HTTPException(status_code=409, detail="更新競合です")
    if row.role == "admin" and body.role == "general" and db.query(User).filter(User.role == "admin").count() == 1:
        raise HTTPException(status_code=400, detail="最後の管理者は一般利用者に変更できません")
    row.display_name = body.display_name
    row.login_id = body.login_id
    row.password_hash = hash_password(body.password)
    row.role = body.role
    row.version += 1
    return UserOut.model_validate(row, from_attributes=True)


@app.delete("/api/users/{user_id}")
def delete_user(user_id: int, body: VersionRequest, x_session_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    """利用者を削除する。"""
    login_user = _get_session_user(db, x_session_token)
    _require_admin(login_user)
    row = db.get(User, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="利用者が存在しません")
    if row.version != body.version:
        raise HTTPException(status_code=409, detail="更新競合です")
    if row.id == login_user.id:
        raise HTTPException(status_code=400, detail="自分自身は削除できません")
    if row.role == "admin" and db.query(User).filter(User.role == "admin").count() == 1:
        raise HTTPException(status_code=400, detail="最後の管理者は削除できません")
    loan_exists = db.query(Equipment).filter(Equipment.loan_user_id == row.id, Equipment.status == "loaned").count() > 0
    if loan_exists:
        raise HTTPException(status_code=400, detail="貸出中の利用者は削除できません")
    db.delete(row)
    return {"ok": True}


@app.post("/api/loans")
def create_loan(body: LoanRequest, x_session_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    """備品貸出を登録する。"""
    user = _get_session_user(db, x_session_token)
    _require_admin(user)
    eq = db.get(Equipment, body.equipment_id)
    if eq is None:
        raise HTTPException(status_code=404, detail="備品が存在しません")
    borrower = db.get(User, body.user_id)
    if borrower is None:
        raise HTTPException(status_code=404, detail="利用者が存在しません")
    if eq.version != body.version:
        raise HTTPException(status_code=409, detail="更新競合です")
    if eq.status != "available":
        raise HTTPException(status_code=400, detail="貸出中の備品です")
    eq.status = "loaned"
    eq.loan_user_id = borrower.id
    eq.loan_date = body.loan_date
    eq.version += 1
    return EquipmentOut.model_validate(eq, from_attributes=True)


@app.post("/api/returns")
def return_equipment(body: ReturnRequest, x_session_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    """備品返却を登録する。"""
    user = _get_session_user(db, x_session_token)
    _require_admin(user)
    eq = db.get(Equipment, body.equipment_id)
    if eq is None:
        raise HTTPException(status_code=404, detail="備品が存在しません")
    if eq.version != body.version:
        raise HTTPException(status_code=409, detail="更新競合です")
    if eq.status != "loaned":
        raise HTTPException(status_code=400, detail="貸出可能備品は返却できません")
    eq.status = "available"
    eq.loan_user_id = None
    eq.loan_date = None
    eq.version += 1
    return EquipmentOut.model_validate(eq, from_attributes=True)
