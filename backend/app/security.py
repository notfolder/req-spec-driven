"""パスワードハッシュ関連。

要件トレーサビリティ:
  要件ID: RQ-NF-PASSWORD-HASH-STORAGE
  設計ID: DS-CL-PASSWORD-SERVICE-NF-PASSWORD-HASH-STORAGE
  要件概要: 平文パスワードを保存せず、ハッシュで照合する。
  設計概要: bcryptでハッシュ化し、ログイン時に照合する。
  呼び出し先: なし
  呼び出し元: DS-CL-AUTH-SERVICE-FT-LOGIN, DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
"""
import bcrypt


def hash_password(password: str) -> str:
    """平文パスワードをbcryptでハッシュ化する。"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """平文パスワードとハッシュを照合する。"""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
