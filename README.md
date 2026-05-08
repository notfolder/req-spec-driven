# 備品管理・貸出管理アプリ

## 起動手順

1. 依存パッケージをインストールします。
   - pip install -r requirements.txt
2. FastAPI を起動します。
   - uvicorn src.backend.main:app --reload --port 8000
3. docker compose で起動する場合は次を実行します。
   - docker compose up --build
4. ブラウザで http://localhost:8080 を開きます。
5. API 疎通確認は http://localhost:8000/api/health を参照します。

## KPI 測定手順

1. 対象備品の資産管理番号を決めます。
2. 一覧画面で該当備品の行を探すまでの時間を計測します。
3. 従来運用の記録と比較して、1件あたり平均10分から5分への短縮可否を確認します。
4. 月次で記録漏れ率と所在不明件数を集計します。
