#!/usr/bin/env bash
# E2Eテスト環境セットアップスクリプト — Neon PostgreSQL 部署マスタDB
# 要件ID: RQ-EX-FETCH-DEPARTMENT-MASTER

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# モードを確認（デフォルト: mock）
MOCK_EXTERNAL_DB="${MOCK_EXTERNAL_DB:-true}"

echo "[setup] MOCK_EXTERNAL_DB=${MOCK_EXTERNAL_DB}"

if [ "${MOCK_EXTERNAL_DB}" = "true" ]; then
  echo "[setup] モックモードでセットアップします"
  # モックJSONファイルの存在確認
  MOCK_DIR="${SCRIPT_DIR}/../mock"
  for f in departments.json users.json mock_department_client.py; do
    if [ ! -f "${MOCK_DIR}/${f}" ]; then
      echo "[ERROR] モックファイルが見つかりません: ${MOCK_DIR}/${f}"
      exit 1
    fi
  done
  echo "[setup] モックファイル確認済み"
else
  echo "[setup] realモードでセットアップします"
  # 環境変数チェック
  if [ -z "${EXTERNAL_DB_URL:-}" ]; then
    echo "[ERROR] EXTERNAL_DB_URL が設定されていません。.env を確認してください"
    exit 1
  fi
  echo "[setup] EXTERNAL_DB_URL 確認済み"
fi

echo "[setup] セットアップ完了"
