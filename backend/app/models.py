"""DBモデル定義。"""
from datetime import date, datetime
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class User(Base):
    """利用者モデル。"""

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    login_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Equipment(Base):
    """備品モデル。"""

    __tablename__ = "equipment"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    equipment_code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="available")
    loan_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    loan_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class SessionModel(Base):
    """ログインセッションモデル。"""

    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    last_accessed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
