# 要件整合確認レポート — Neon PostgreSQL 部署マスタDB

作成日: 2026-05-06  
入力要件: `.history/20260506-add-department-and-reservation/change_requirements.md`（変更要件定義書）

---

## 1. 入力要件の識別情報

| 項目 | 内容 |
|---|---|
| 要件書種別 | 変更要件定義書（change_requirements） |
| パス | `.history/20260506-add-department-and-reservation/change_requirements.md` |
| 変更対象システム | 備品管理・貸出管理アプリ |
| 外部システム | Neon PostgreSQL（demo_departments, demo_users） |

---

## 2. 一致している要件一覧

| RQ-ID | 内容 | 整合理由 |
|---|---|---|
| RQ-EX-FETCH-DEPARTMENT-MASTER（部分） | 外部DB（Neon PostgreSQL）から部署情報を取得する | demo_departments アクセスは整合。ただし demo_users の追加が必要（詳細は不整合3） |
| RQ-DT-DEPARTMENT-EXTERNAL | 外部データとして部署データを扱う（内部DBに保存しない） | 「内部DBに保存しない」は整合。ただし demo_users も取得対象となる |
| RQ-DT-EXTERNAL-DB-NEON | Neon PostgreSQL（demo_departments）への接続仕様 | 接続方式・環境変数・SSL設定が整合 |
| RQ-NF-EXTERNAL-DB-TIMEOUT | 外部DB接続タイムアウト5秒以内 | 実測で接続確認済み。タイムアウト設定で対応可能 |
| RQ-NF-EXTERNAL-DB-READONLY | SELECT のみ実行禁止 | neondb_ownerは書き込み権限あり。アプリ側で徹底が必要 |
| RQ-UI-BORROWER-LIST-DEPT-COLUMN | 利用者一覧に部署名列を追加 | 外部DBからの動的取得で実現可能 |
| RQ-UI-LOAN-FORM-DEPT-DISPLAY | 貸出登録画面に部署名表示 | 外部DBからの動的取得で実現可能 |
| RQ-UI-ADMIN-LIST-DEPT-DISPLAY | 管理者向け備品一覧に部署名表示 | 外部DBからの動的取得で実現可能 |

---

## 3. 不整合要件一覧

### 不整合1（矛盾）: 内部DBへの department_id 追加

| 項目 | 内容 |
|---|---|
| RQ-ID | RQ-DT-BORROWER-DEPT-ATTRIBUTE |
| 記載内容 | 「利用者エンティティに部署ID（department_id）属性を追加する」 |
| 不整合種別 | 矛盾 |
| 外部仕様との差分 | ユーザー確認で「今回内部DBは絶対に変更しません」と確定。内部 SQLite には department_id カラムを追加しない |

### 不整合2（矛盾）: 利用者登録フォームへの部署選択UI

| 項目 | 内容 |
|---|---|
| RQ-ID | RQ-FT-SELECT-DEPARTMENT、RQ-UI-BORROWER-FORM-DEPT-FIELD |
| 記載内容 | 「利用者登録・編集時に部署をドロップダウンで選択できる機能」「利用者登録・編集画面に部署選択ドロップダウンを追加」 |
| 不整合種別 | 矛盾 |
| 外部仕様との差分 | 部署は登録時に選択するのではなく、表示時に外部DB（demo_users）から自動取得する。登録フォームへの部署UIは不要 |

### 不整合3（不足）: demo_users テーブルへのアクセス

| 項目 | 内容 |
|---|---|
| RQ-ID | 新規（RQ-EX-FETCH-DEPARTMENT-MASTER の更新）|
| 記載内容 | 変更要件定義書には demo_departments のみ記載 |
| 不整合種別 | 不足 |
| 外部仕様との差分 | 部署名の取得には demo_users（login_id ↔ user_id 照合）経由が必要。demo_departments だけでは部署名を導出できない |

### 不整合4（不足）: ログインIDによる部署名自動取得機能

| 項目 | 内容 |
|---|---|
| RQ-ID | 新規（RQ-FT-FETCH-DEPT-BY-LOGIN-ID）|
| 記載内容 | 動的取得の仕様が機能要件として記載されていない |
| 不整合種別 | 不足 |
| 外部仕様との差分 | 「内部利用者のlogin_idでdemo_usersを検索→department_idを取得→demo_departmentsで部署名を取得、一致なしは「不明」と表示」という仕様が機能要件に明示されていない |

---

## 4. 修正方針

| 不整合 | 修正内容 |
|---|---|
| 不整合1 | RQ-DT-BORROWER-DEPT-ATTRIBUTE を変更要件定義書から削除する（[削除] として deprecated） |
| 不整合2 | RQ-FT-SELECT-DEPARTMENT・RQ-UI-BORROWER-FORM-DEPT-FIELD を変更要件定義書から削除する |
| 不整合3 | RQ-EX-FETCH-DEPARTMENT-MASTER を更新し demo_users へのアクセスも明記する |
| 不整合4 | 新要件 RQ-FT-FETCH-DEPT-BY-LOGIN-ID を変更要件定義書に追加する |

---

## 5. 修正後の確認結果

修正後の change_requirements.md（同ファイルを直接更新）にて以下を確認済み。

| 確認項目 | 結果 |
|---|---|
| 内部DBへの変更が要件に含まれないこと | ✅ RQ-DT-BORROWER-DEPT-ATTRIBUTE 削除済み |
| 登録フォームへの部署UIが要件に含まれないこと | ✅ RQ-FT-SELECT-DEPARTMENT・RQ-UI-BORROWER-FORM-DEPT-FIELD 削除済み |
| demo_users テーブルへのアクセスが要件に明記されていること | ✅ RQ-EX-FETCH-DEPARTMENT-MASTER 更新済み |
| ログインIDによる部署名自動取得が機能要件に明記されていること | ✅ RQ-FT-FETCH-DEPT-BY-LOGIN-ID 追加済み |
| 照合失敗時の「不明」表示が要件に明記されていること | ✅ RQ-FT-FETCH-DEPT-BY-LOGIN-ID に明記 |
| すべての RQ-BK-* との紐づきが双方向で成立していること | ✅ 確認済み |

---

## 6. 設計フェーズ進行可否

**✅ 設計フェーズへ進んでよい**

- 全不整合（不整合1〜4）を解消済み
- 採用ライブラリ確定: SQLAlchemy 2.0 + psycopg2-binary
- 未解消の不整合なし
- モック方式確定: 固定レスポンスファイル方式（RQ-EX-USE-FIXED-RESPONSE-MOCK）

### 設計フェーズへの引き継ぎ事項

| 引き継ぎ項目 | 内容 |
|---|---|
| 調査レポート | `external/neon-department-db/docs/research.md` |
| 整合確認レポート | `external/neon-department-db/docs/alignment_report.md` |
| 環境変数テンプレート | `external/neon-department-db/.env.example` |
| 採用ライブラリ | SQLAlchemy 2.0 + psycopg2-binary |
| 接続設定 | NullPool + pool_pre_ping=True（コールドスタート対策） |
| 接続文字列環境変数 | `EXTERNAL_DB_URL` |
| モック方式 | 固定レスポンスファイル方式（`external/neon-department-db/mock/`） |
| 部署名取得ロジック | login_id → demo_users.user_id → department_id → demo_departments.department_name。不一致時は「不明」を返す |
| セキュリティ注意 | neondb_owner は書き込み権限あり。設計にて読み取り専用ロール作成または SELECT 以外の実行防止を規定すること |
