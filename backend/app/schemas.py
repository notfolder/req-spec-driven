"""API入出力スキーマ。"""
from datetime import date
from pydantic import BaseModel


class LoginRequest(BaseModel):
    login_id: str
    password: str


class UserOut(BaseModel):
    id: int
    display_name: str
    login_id: str
    role: str
    version: int


class EquipmentOut(BaseModel):
    id: int
    equipment_code: str
    name: str
    status: str
    loan_user_id: int | None
    loan_date: date | None
    version: int


class CreateUserRequest(BaseModel):
    display_name: str
    login_id: str
    password: str
    role: str


class UpdateUserRequest(CreateUserRequest):
    version: int


class CreateEquipmentRequest(BaseModel):
    equipment_code: str
    name: str


class UpdateEquipmentRequest(CreateEquipmentRequest):
    version: int


class VersionRequest(BaseModel):
    version: int


class LoanRequest(BaseModel):
    equipment_id: int
    user_id: int
    loan_date: date
    version: int


class ReturnRequest(BaseModel):
    equipment_id: int
    version: int
