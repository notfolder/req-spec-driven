"""
pytest ルート conftest — sys.path 設定と .env 読み込み。
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをパスに追加（src / mock パッケージを解決するため）
sys.path.insert(0, str(Path(__file__).parent))

# プロジェクトルートの .env を読み込む（EXTERNAL_DB_URL 等）
_root_env = Path(__file__).parent.parent.parent / ".env"
if _root_env.exists():
    load_dotenv(_root_env)
