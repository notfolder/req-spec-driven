"""SQLAlchemyセッションとDB初期化。

要件トレーサビリティ:
  要件ID: RQ-DT-APP-DATABASE-REQUIRED
  設計ID: DS-SC-DATABASE-REQUIRED-DT-APP-DATABASE-REQUIRED
  要件概要: 備品、利用者、貸出状態を永続化する。
  設計概要: API単位でトランザクションを開始し成功時コミット、失敗時ロールバックする。
  呼び出し先: DS-SC-SQLITE-DATABASE-DT-APP-DATABASE-REQUIRED
  呼び出し元: DS-MD-BACKEND-APP-FT-MANAGE-EQUIPMENT
"""
from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base()


def create_session_factory(db_path: str) -> sessionmaker:
    """セッションファクトリを作成する。"""
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db(session_factory: sessionmaker) -> None:
    """テーブルを作成する。"""
    Base.metadata.create_all(bind=session_factory.kw["bind"])


def db_session_dependency(session_factory: sessionmaker) -> Generator[Session, None, None]:
    """FastAPI依存で1リクエスト1トランザクションを提供する。"""
    db = session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
