# 外部連携 事前確認レポート — Neon 部署マスタDB

作成日: 2026-05-06

---

## 1. 連携先概要

| 項目 | 内容 |
|---|---|
| システム名 | Neon Serverless PostgreSQL（部署マスタDB） |
| 目的 | 備品管理・貸出管理アプリへの部署名表示（SELECT のみ） |
| DBエンジン | PostgreSQL 17.8 |
| ホスト種別 | Neon 接続プーラー経由（PgBouncer） |
| リージョン | ap-southeast-1（AWS） |
| 対象テーブル | `demo_departments`、`demo_users` |

### 取得対象スキーマ

#### demo_departments
| カラム名 | 型 | NULL | 説明 |
|---|---|---|---|
| department_id | VARCHAR | NOT NULL (PK) | 部署ID（例: D001） |
| department_name | VARCHAR | NOT NULL | 部署名（例: 営業部） |

#### demo_users
| カラム名 | 型 | NULL | 説明 |
|---|---|---|---|
| user_id | VARCHAR | NOT NULL (PK) | ユーザーID |
| user_name | VARCHAR | NOT NULL | ユーザー名 |
| department_id | VARCHAR | NOT NULL | 所属部署ID（FK→demo_departments） |

---

## 2. 接続可否判定

| 項目 | 結果 |
|---|---|
| 接続確認 | **成功**（2026-05-06 実測） |
| テーブル一覧取得 | 成功（demo_departments / demo_users） |
| SELECT クエリ実行 | 成功（部署データ5件確認済み） |
| 最大接続数 | 901（アプリの同時接続20人に対して余裕あり） |
| 現在の接続数 | 13（実測値） |

**判定: 接続可能**

---

## 3. 認証方式

| 項目 | 内容 |
|---|---|
| 認証方式 | ユーザー名 + パスワード（直接DB認証） |
| SSL | `sslmode=require`（必須） |
| チャネルバインディング | `channel_binding=require`（必須） |
| 接続エンドポイント | 接続プーラー（PgBouncer）経由 |
| 環境変数名（推奨） | `EXTERNAL_DB_URL` |

> **⚠️ セキュリティ注意**: 現在の接続ユーザー（`neondb_owner`）は書き込み権限を持つ。
> アプリには読み取り専用ロールの使用を強く推奨する。
> 環境変数 `EXTERNAL_DB_URL` に接続文字列を格納し、コードに直書きしない。

---

## 4. 主要制限

| 制限項目 | 内容 |
|---|---|
| アクセス種別 | 読み取り専用（SELECT のみ）として利用する |
| Neon オートサスペンド | 無操作5分後にDB停止 → 初回接続時に最大数秒の遅延が発生する可能性あり |
| 接続プーラー制約 | PgBouncer 経由のため、`PREPARE` 文・`LISTEN/NOTIFY` 等の一部機能は利用不可 |
| レート制限 | 明示的な制限なし（max_connections=901） |
| タイムアウト | 明示的な設定なし（アプリ側でコネクションタイムアウトを設定すること） |
| ライセンス | 社内データのため法務制約は不明。要件定義時に確認が必要 |

---

## 5. 後続 `isdd-external-research` の調査対象範囲

変更要件定義書（`change_requirements.md`）出力後に実施する `isdd-external-research` で以下を確認すること。

| 調査項目 | 優先度 | 理由 |
|---|---|---|
| 読み取り専用ロール作成の要否 | 高 | `neondb_owner` に書き込み権限があるため、最小権限の原則を適用すべき |
| Neon オートサスペンド対策（ウォームアップ接続） | 中 | 冷起動遅延が応答時間要件（3秒以内）に影響する可能性あり |
| `demo_departments` の更新頻度 | 中 | 部署マスタがどの程度変更されるか（キャッシュ戦略に影響） |
| `demo_users` の利用用途 | 低 | 予約機能との関連性を確認 |

---

## 6. 要件定義に進んでよいかの判定

**✅ 要件定義に進んでよい**

- 接続: 実測で確認済み
- スキーマ: `demo_departments`（部署ID・部署名）が確認済み
- 認証: 接続文字列を環境変数 `EXTERNAL_DB_URL` で管理する前提で要件を定義できる
- 制約: オートサスペンドによる遅延リスクを要件・設計に盛り込む必要あり

### 要件定義に必ず盛り込む制約事項

1. 外部DB接続の環境変数は `EXTERNAL_DB_URL` とし、アプリ起動時に必須チェックを行う
2. 外部DBへは SELECT のみを実行し、INSERT/UPDATE/DELETE は行わない
3. Neon オートサスペンドを考慮し、接続失敗時のフォールバック動作（エラー表示）を定義する
4. 部署マスタはアプリ内にキャッシュしない（常に外部DBから取得する）か、キャッシュ戦略を明示する

---

## 引き継ぎ情報（isdd-change-req へ）

| 項目 | 内容 |
|---|---|
| precheck_report パス | `external/neon-department-db/docs/precheck_report.md` |
| 接続方式 | PostgreSQL 直接接続（接続プーラー経由） |
| 対象テーブル | `demo_departments`（department_id, department_name） |
| 認証環境変数 | `EXTERNAL_DB_URL` |
| 要件定義への制約 | 上記「要件定義に必ず盛り込む制約事項」4点を適用すること |
| 詳細調査が必要な論点 | 読み取り専用ロール、オートサスペンド対策、部署マスタ更新頻度 |
