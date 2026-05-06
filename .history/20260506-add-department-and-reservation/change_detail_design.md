# 変更詳細設計書 — 部署マスタ連携 & 備品予約機能追加

作成日: 2026-05-06  
対応変更要件定義書: `.history/20260506-add-department-and-reservation/change_requirements.md`

---

## 1. 言語・フレームワーク（変更分）

### [追加] 新規ライブラリ

| DS-ID | 対象 | 採用技術 | バージョン | 選定理由 |
|---|---|---|---|---|
| DS-MD-EXTERNAL-DEPT-DB-EX-FETCH-DEPARTMENT-MASTER | 外部DB連携 | SQLAlchemy 2.0 + psycopg2-binary | 2.0.x / 2.9.x | Neon PostgreSQL への接続。NullPool + channel_binding=require に対応する唯一の構成。既存の SQLAlchemy 統一方針に整合 |
| DS-MD-DOTENV-EX-FETCH-DEPARTMENT-MASTER | 環境変数 | python-dotenv | 1.x | 外部DB接続 URL を .env から読み込むため |

変更なし。その他の技術スタック（Vue 3 + Vuetify 3、FastAPI、SQLite、Playwright）は既存設計 `docs/detail_design.md` セクション1 を参照。

---

## 2. システム構成（変更分）

### [追加] 新規コンポーネント

| DS-ID | コンポーネント | 役割 | 根拠要件 |
|---|---|---|---|
| DS-MD-EXTERNAL-DEPT-DB-EX-FETCH-DEPARTMENT-MASTER | 外部DB（Neon PostgreSQL） | 部署マスタ（demo_departments・demo_users）を保持する外部 PostgreSQL | RQ-EX-FETCH-DEPARTMENT-MASTER |

### [追加] 更新後のシステム全体構成図

```mermaid
graph LR
    Browser[ブラウザ] --> Nginx["Nginx\nVue3 SPA配信\n/api/ プロキシ"]
    Nginx --> FastAPI["FastAPI\nバックエンド"]
    FastAPI --> SQLite[("SQLite\n内部DB")]
    FastAPI --> NeonDB[("Neon PostgreSQL\n外部DB（部署マスタ）")]
```

### [追加] 更新後のネットワーク構成図

```mermaid
graph TD
    user[ブラウザ] --> frontend
    subgraph "Docker Compose ネットワーク"
        frontend["frontend\nNginx:80"]
        backend["backend\nuvicorn:8000（非公開）"]
        frontend -- "/api/ proxy" --> backend
        backend --> db[("data/app.db\nSQLiteボリューム")]
    end
    backend -- "EXTERNAL_DB_URL\nSSL必須" --> neon[("Neon PostgreSQL\n外部DB")]
```

---

## 3. データベース設計（変更分）

変更なし。既存設計 `docs/detail_design.md` セクション3 を参照（SQLite採用理由・既存3テーブル定義・リレーション図）。

### [削除] deprecated 設計要素

| 設計要素 | deprecated 理由 |
|---|---|
| 「外部DB連携なし（RQ-DT-NO-EXTERNAL-DB）」の記述 | 外部DB（Neon PostgreSQL）への接続が追加されるため |

### [追加] equipment テーブルへのステータス拡張

**DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY（更新）:**

status カラムの許容値を 'available'・'reserved'・'loaned' の3値に拡張する。

| カラム名 | 型 | 制約 | 変更内容 |
|---|---|---|---|
| status | TEXT | NOT NULL DEFAULT 'available' | 許容値: 'available'（在庫）・'reserved'（予約済み）・'loaned'（貸出中）に拡張 |

**ステータス遷移規則 (DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY):**

| 遷移 | 条件 | 操作 |
|---|---|---|
| available → reserved | 予約作成時に有効な予約が初めて登録される | ReservationService.create 内で自動更新 |
| reserved → available | 予約キャンセル後に有効な予約が0件になる（かつ貸出中でない） | ReservationService.cancel 内で自動更新 |
| available/reserved → loaned | 貸出操作 | EquipmentService.loan 内で更新（既存） |
| loaned → reserved | 返却操作後に end_date < 返却日 の予約を削除し、残予約が1件以上ある | EquipmentService.return_equipment 内で更新 |
| loaned → available | 返却操作後に end_date < 返却日 の予約を削除し、残予約が0件 | EquipmentService.return_equipment 内で更新 |

### [追加] reservation テーブル

**DS-SC-RESERVATION-DT-RESERVATION-ENTITY:**

| カラム名 | 型 | 制約 | 説明 |
|---|---|---|---|
| reservation_id | TEXT | PRIMARY KEY | UUID 形式の予約ID（自動生成） |
| equipment_id | TEXT | NOT NULL, FK→equipment.equipment_id ON DELETE CASCADE | 予約対象の備品ID |
| user_login_id | TEXT | NOT NULL, FK→user.login_id | 予約者のログインID |
| start_date | TEXT | NOT NULL | 予約開始日（ISO 8601形式、例: 2026-06-01） |
| end_date | TEXT | NOT NULL | 予約終了日（ISO 8601形式、例: 2026-06-05）。start_date 以降であること |

ON DELETE CASCADE を equipment.equipment_id FK に設定する。備品削除時に対象備品の予約レコードを全て自動削除する。

### [追加] 更新後のリレーション図

```mermaid
erDiagram
    equipment {
        TEXT equipment_id PK
        TEXT name
        TEXT status
    }
    user {
        TEXT login_id PK
        TEXT display_name
        TEXT password_hash
        TEXT role
    }
    loan_state {
        TEXT equipment_id PK
        TEXT user_login_id
        TEXT loan_date
    }
    reservation {
        TEXT reservation_id PK
        TEXT equipment_id FK
        TEXT user_login_id FK
        TEXT start_date
        TEXT end_date
    }
    equipment ||--o| loan_state : "has"
    user ||--o{ loan_state : "borrowed_by"
    equipment ||--o{ reservation : "has"
    user ||--o{ reservation : "made_by"
```

### [追加] 追加データ整合性・業務制約

| DS-ID | 制約 | 実装箇所 |
|---|---|---|
| DS-FN-VALIDATE-RESERVATION-CONFLICT-NF-RESERVATION-CONFLICT-PREVENTION | 同一備品に対し期間が1日以上重なる予約の登録を禁止する。SELECT COUNT 後に INSERT を同一トランザクション内で実行し、SQLite のライトロックで競合を防ぐ | ReservationService.create |
| DS-FN-VALIDATE-LOAN-AVAILABLE-RESERVED-FT-LOAN-EQUIPMENT | 貸出操作は status が 'available' または 'reserved' の場合のみ許可する（既存の 'available' のみから拡張） | EquipmentService.loan |
| DS-FN-VALIDATE-RESERVATION-CANCEL-FT-CANCEL-RESERVATION | 予約のキャンセルは予約者本人または管理者のみ可能 | ReservationService.cancel |

---

## 4. アーキテクチャ設計（変更分）

### 4.1 外部設計

#### [削除] deprecated 設計要素

| 設計要素 | deprecated 理由 |
|---|---|
| 「外部連携なし（RQ-EX-NO-EXTERNAL-INTEGRATION）」の記述 | Neon PostgreSQL への外部連携が追加されるため |
| 「外部DB連携なし（RQ-DT-NO-EXTERNAL-DB）」の記述 | 同上 |

#### 画面一覧（変更分）

**[追加] 新規画面**

| DS-ID | 画面名 | 対応 RQ-UI-ID | 利用者 |
|---|---|---|---|
| DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN | 備品別予約詳細・カレンダー画面 | RQ-UI-RESERVATION-CALENDAR-SCREEN | 全利用者 |
| DS-CL-RESERVATION-FORM-VIEW-UI-RESERVATION-FORM-SCREEN | 予約登録画面 | RQ-UI-RESERVATION-FORM-SCREEN | 全利用者 |

**[追加] 既存画面への追加仕様**

| DS-ID | 画面名 | 追加内容 | 対応 RQ-UI-ID |
|---|---|---|---|
| DS-CL-USER-LIST-VIEW-UI-BORROWER-LIST-SCREEN | 利用者一覧画面 | 部署列を追加（非同期取得、初期表示は「取得中...」） | RQ-UI-BORROWER-LIST-DEPT-COLUMN |
| DS-CL-LOAN-FORM-VIEW-UI-LOAN-FORM-SCREEN | 貸出登録画面 | ドロップダウン選択肢を「利用者名（部署名）」形式に変更（部署は非同期取得） | RQ-UI-LOAN-FORM-DEPT-DISPLAY |
| DS-CL-ADMIN-EQUIPMENT-LIST-VIEW-UI-ADMIN-EQUIPMENT-LIST-SCREEN | 管理者向け備品一覧画面 | 貸出先表示を「利用者名（部署名）」形式に変更・予約ステータス追加・「予約状況」ボタン追加 | RQ-UI-ADMIN-LIST-DEPT-DISPLAY, RQ-UI-ADMIN-LIST-RESERVATION-STATUS |
| DS-CL-GENERAL-EQUIPMENT-LIST-VIEW-UI-GENERAL-EQUIPMENT-LIST-SCREEN | 一般利用者向け備品一覧画面 | 予約ステータス（「予約済み」）追加・「予約状況」ボタン追加 | RQ-UI-GENERAL-LIST-RESERVATION-STATUS |

#### 画面 AA モックアップ（追加・変更分）

**DS-CL-ADMIN-EQUIPMENT-LIST-VIEW-UI-ADMIN-EQUIPMENT-LIST-SCREEN: 管理者向け備品一覧画面（変更後）**
```
┌─────────────────────────────────────────────────────────────────────┐
│ 備品一覧 (管理者)                      [利用者管理]  [ログアウト]  │
├─────────────────────────────────────────────────────────────────────┤
│ [+ 備品登録]                                                        │
├────────┬──────────┬──────────┬─────────────────────┬──────────────┤
│ 備品ID │ 備品名   │ 状態     │ 貸出先（部署）      │ 操作         │
├────────┼──────────┼──────────┼─────────────────────┼──────────────┤
│ PC-001 │MacBook A │ 貸出中   │山田太郎（営業部）   │[返却][予約状況]│
├────────┼──────────┼──────────┼─────────────────────┼──────────────┤
│ PC-002 │MacBook B │ 予約済み │                     │[貸出][削除][予約状況]│
├────────┼──────────┼──────────┼─────────────────────┼──────────────┤
│ PC-003 │Surface C │ 在庫     │                     │[貸出][削除][予約状況]│
└────────┴──────────┴──────────┴─────────────────────┴──────────────┘
```
※ 部署名は画面描画後に非同期取得。取得前は「取得中...」を表示。
※ 「貸出」ボタンは status が 'available' または 'reserved' の場合に表示。

**DS-CL-GENERAL-EQUIPMENT-LIST-VIEW-UI-GENERAL-EQUIPMENT-LIST-SCREEN: 一般利用者向け備品一覧画面（変更後）**
```
┌──────────────────────────────────────────────────────────┐
│ 備品一覧 (閲覧のみ)                       [ログアウト]   │
├────────┬──────────┬──────────────┬──────────────────────┤
│ 備品ID │ 備品名   │ 状態         │ 操作                 │
├────────┼──────────┼──────────────┼──────────────────────┤
│ PC-001 │ MacBook A│ 貸出中       │ [予約状況]           │
├────────┼──────────┼──────────────┼──────────────────────┤
│ PC-002 │ MacBook B│ 予約済み     │ [予約状況]           │
├────────┼──────────┼──────────────┼──────────────────────┤
│ PC-003 │ Surface C│ 在庫         │ [予約状況]           │
└────────┴──────────┴──────────────┴──────────────────────┘
```

**DS-CL-LOAN-FORM-VIEW-UI-LOAN-FORM-SCREEN: 貸出登録画面（変更後）**
```
┌──────────────────────────────────────────┐
│ 貸出登録                                 │
├──────────────────────────────────────────┤
│ 備品ID  : PC-002                         │
│ 備品名  : MacBook B                      │
│                                          │
│ 貸出先  [▼ 山田太郎（取得中...）]       │
│ 貸出日  [2026-05-05            ]         │
│                                          │
│        [登録する]  [キャンセル]          │
└──────────────────────────────────────────┘
```
※ ドロップダウン選択肢は「利用者名（部署名）」形式。部署は画面表示後に非同期取得する。取得前は「取得中...」を表示。

**DS-CL-USER-LIST-VIEW-UI-BORROWER-LIST-SCREEN: 利用者一覧画面（変更後）**
```
┌────────────────────────────────────────────────────────────────┐
│ 利用者一覧              [備品一覧へ戻る]  [ログアウト]         │
├────────────────────────────────────────────────────────────────┤
│ [+ 利用者登録]                                                 │
├────────────┬──────────┬──────────────┬────────────┬──────────┤
│ 利用者名   │ログインID│ 部署         │ 権限       │ 操作     │
├────────────┼──────────┼──────────────┼────────────┼──────────┤
│ 山田 太郎  │ yamada   │ 取得中...    │ 管理者     │[編集][削除]│
├────────────┼──────────┼──────────────┼────────────┼──────────┤
│ 鈴木 花子  │ suzuki   │ 開発部       │ 一般利用者 │[編集][削除]│
└────────────┴──────────┴──────────────┴────────────┴──────────┘
```
※ 部署列は画面描画後に全利用者分を非同期並行取得する。取得前は「取得中...」。一致なし・接続失敗は「不明」を表示。

**DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN: 備品別予約詳細・カレンダー画面（新規）**
```
┌──────────────────────────────────────────────────────────────────┐
│ 備品予約状況                               [戻る]  [ログアウト]  │
├──────────────────────────────────────────────────────────────────┤
│ 備品ID: PC-002  備品名: MacBook B  状態: 予約済み               │
├──────────────────────────────────────────────────────────────────┤
│ 予約一覧                                                         │
├─────────────────────────┬──────────┬──────────┬────────────────┤
│ 予約者名（部署）         │ 開始日   │ 終了日   │ 操作           │
├─────────────────────────┼──────────┼──────────┼────────────────┤
│ 田中太郎（営業部）       │ 06-01    │ 06-05    │ [キャンセル]   │
├─────────────────────────┼──────────┼──────────┼────────────────┤
│ 鈴木花子（開発部）       │ 06-10    │ 06-15    │                │
├──────────────────────────────────────────────────────────────────┤
│ ≪ 2026年6月 ≫                                      [予約する]   │
│  月  火  水  木  金  土  日                                      │
│                    1   2   3   4   5 ←予約済みハイライト        │
│   6   7   8   9  10  11  12                                      │
│  13  14  15  16  17  18  19                                      │
└──────────────────────────────────────────────────────────────────┘
```
※ 「キャンセル」ボタンは予約者本人の予約行に表示。管理者は全行に表示。
※ 「予約する」ボタンは備品ステータスに関わらず常に表示。

**DS-CL-RESERVATION-FORM-VIEW-UI-RESERVATION-FORM-SCREEN: 予約登録画面（新規）**
```
┌──────────────────────────────────────────────────────┐
│ 予約登録                                             │
├──────────────────────────────────────────────────────┤
│ 備品ID  : PC-002                                     │
│ 備品名  : MacBook B                                  │
│                                                      │
│ 開始日  [2026-06-10              ]（必須）           │
│ 終了日  [2026-06-15              ]（必須）           │
│ ※ 管理者のみ: 予約者 [▼ 利用者を選択]             │
│                                                      │
│         [登録する]  [キャンセル]                     │
│                                                      │
│ ※ 重複エラー時:「指定期間は既に予約されています」   │
└──────────────────────────────────────────────────────┘
```

#### 外部システム連携（変更分）

**[追加] 外部DB連携一覧**

| DS-ID | 連携先 | 方向 | 実装ライブラリ |
|---|---|---|---|
| DS-MD-EXTERNAL-DEPT-DB-EX-FETCH-DEPARTMENT-MASTER | Neon PostgreSQL（部署マスタ） | 読み取り（SELECT のみ） | external/neon-department-db/src/department_client.py |

**外部DB連携データフロー図 (DS-MD-EXTERNAL-DEPT-DB-EX-FETCH-DEPARTMENT-MASTER):**

```mermaid
sequenceDiagram
    participant FE as フロントエンド
    participant BE as FastAPI
    participant Dept as DepartmentService
    participant Client as RealDepartmentClient / MockDepartmentClient
    participant NeonDB as Neon PostgreSQL

    FE->>BE: GET /api/department/by-login-id?login_id=yamada
    BE->>Dept: get_department_name("yamada")
    Dept->>Client: fetch_department_name_by_login_id("yamada")
    Client->>NeonDB: SELECT d.department_name FROM demo_users u JOIN demo_departments d ON u.department_id=d.department_id WHERE u.user_id='yamada'
    NeonDB-->>Client: "営業部"
    Client-->>Dept: "営業部"
    Dept-->>BE: "営業部"
    BE-->>FE: {"department_name": "営業部"}
```

### 4.2 APIエンドポイント設計（変更分）

**[追加] 新規 API エンドポイント**

| DS-ID | メソッド | パス | 権限 | 入力スキーマ | 出力スキーマ | エラー |
|---|---|---|---|---|---|---|
| DS-IF-DEPT-NAME-BY-LOGIN-ID-FT-DEPT-NAME-API | GET | /api/department/by-login-id | 要ログイン | login_id（クエリパラメータ） | DeptNameResponse | 401 |
| DS-IF-RESERVATION-LIST-FT-VIEW-RESERVATION-CALENDAR | GET | /api/equipment/{id}/reservations | 要ログイン | なし | ReservationResponse[] | 401/404 |
| DS-IF-RESERVATION-CREATE-FT-MAKE-RESERVATION | POST | /api/equipment/{id}/reservations | 要ログイン | ReservationCreate | ReservationResponse | 401/404/409 |
| DS-IF-RESERVATION-DELETE-FT-CANCEL-RESERVATION | DELETE | /api/reservations/{reservation_id} | 要ログイン | なし | 204 | 401/403/404 |

**DeptNameResponse スキーマ (DS-EV-DEPT-NAME-RESPONSE-FT-DEPT-NAME-API):**
- `department_name`: str — 部署名。照合失敗・外部DB接続失敗時は "不明"

**ReservationCreate スキーマ (DS-EV-RESERVATION-CREATE-FT-MAKE-RESERVATION):**
- `start_date`: str（YYYY-MM-DD形式、必須）
- `end_date`: str（YYYY-MM-DD形式、必須、start_date 以降）
- `user_login_id`: str（管理者のみ指定可。一般利用者は自動的に自分のID）

**ReservationResponse スキーマ (DS-EV-RESERVATION-RESPONSE-FT-VIEW-RESERVATION-CALENDAR):**
- `reservation_id`: str
- `equipment_id`: str
- `user_login_id`: str
- `user_display_name`: str（JOIN で取得）
- `start_date`: str
- `end_date`: str

### 4.3 内部設計（変更分）

#### 処理フロー図（追加分）

**予約登録処理 (DS-FN-PROCESS-CREATE-RESERVATION-FT-MAKE-RESERVATION):**

```mermaid
flowchart TD
    A[POST /api/equipment/{id}/reservations 受信] --> B[ログイン確認]
    B -->|401| X[401 Unauthorized]
    B --> C[equipment 取得]
    C -->|なし| Y[404 Not Found]
    C --> D{一般利用者？}
    D -->|一般利用者| E[user_login_id を自分のIDに固定]
    D -->|管理者| F[user_login_id を入力値から取得]
    E --> G[トランザクション開始]
    F --> G
    G --> H[同一備品の重複期間チェック SELECT COUNT]
    H -->|重複あり| Z[409 Conflict 「指定期間は既に予約されています」]
    H -->|重複なし| I[reservation レコード作成]
    I --> J{equipment.status == available？}
    J -->|available| K[equipment.status を reserved に更新]
    J -->|reserved/loaned| L[status 変更なし]
    K --> M[コミット → 201 Created]
    L --> M
```

**予約キャンセル処理 (DS-FN-PROCESS-CANCEL-RESERVATION-FT-CANCEL-RESERVATION):**

```mermaid
flowchart TD
    A[DELETE /api/reservations/{id} 受信] --> B[ログイン確認]
    B -->|401| X[401]
    B --> C[reservation 取得]
    C -->|なし| Y[404]
    C --> D{本人または管理者？}
    D -->|違う| Z[403 Forbidden]
    D -->|OK| E[トランザクション開始]
    E --> F[reservation 削除]
    F --> G[同一備品の残予約数を確認]
    G -->|0件かつ status != loaned| H[equipment.status を available に更新]
    G -->|1件以上 または loaned| I[status 変更なし]
    H --> J[コミット → 204 No Content]
    I --> J
```

**返却処理（更新後）(DS-FN-PROCESS-RETURN-UPDATE-STATUS-FT-RETURN-EQUIPMENT):**

```mermaid
flowchart TD
    A[POST /api/equipment/{id}/return 受信] --> B[管理者権限チェック]
    B -->|403| X[403]
    B --> C[loan_state 取得]
    C -->|なし| Y[404]
    C --> D[トランザクション開始]
    D --> E[loan_state 削除]
    E --> F[end_date < 返却日 の予約を削除 ReservationRepository.delete_expired_by_equipment]
    F --> G[同一備品の残予約数確認]
    G -->|1件以上| H[equipment.status を reserved に更新]
    G -->|0件| I[equipment.status を available に更新]
    H --> J[コミット → 200 OK]
    I --> J
```

**部署名非同期取得処理 (DS-FN-FETCH-DEPT-ASYNC-FT-FETCH-DEPT-BY-LOGIN-ID):**

```mermaid
flowchart TD
    A[画面描画完了] --> B[ユーザー一覧または貸出先を取得]
    B --> C[各 login_id に対して Fetch API を並行呼び出し]
    C --> D[GET /api/department/by-login-id?login_id=xxx]
    D --> E{レスポンス？}
    E -->|成功| F[department_name で「取得中...」を置き換え]
    E -->|失敗・タイムアウト| G[「不明」で「取得中...」を置き換え]
```

#### トランザクション・排他制御（追加分）

| DS-ID | 処理 | トランザクション境界 | ロールバック条件 |
|---|---|---|---|
| DS-FN-TRANSACTION-RESERVATION-DT-RESERVATION-ENTITY | 予約登録 | 重複チェック SELECT + reservation INSERT + equipment.status 更新を1トランザクション | どれか失敗時にロールバック。SQLite のライトロックで同時予約の競合を防ぐ |
| DS-FN-TRANSACTION-CANCEL-RESERVATION-DT-RESERVATION-ENTITY | 予約キャンセル | reservation DELETE + equipment.status 更新（条件付き）を1トランザクション | 失敗時にロールバック |
| DS-FN-TRANSACTION-RETURN-UPDATE-FT-RETURN-EQUIPMENT | 返却処理（更新） | loan_state DELETE + end_date < 返却日の予約削除 + 残予約数確認 + equipment.status 更新を1トランザクション | 失敗時にロールバック |

---

## 5. クラス設計（変更分）

### [追加] 外部 DB 連携クラス（external/neon-department-db/src/）

| DS-ID | クラス名 | 役割 | SOLID適合 |
|---|---|---|---|
| DS-CL-REAL-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER | RealDepartmentClient | get_external_db_engine + fetch_department_name_by_login_id をクラスに包み MockDepartmentClient と同一インターフェースを提供する | S: 外部DB接続のみ |

**RealDepartmentClient の責務・主要メソッド:**

| 種別 | 名前 | 説明 |
|---|---|---|
| メソッド | __init__() | get_external_db_engine() でエンジンを生成して保持する |
| メソッド | fetch_department_name_by_login_id(login_id: str) → Optional[str] | fetch_department_name_by_login_id(engine, login_id) を呼び出して結果を返す |

### [追加] 新規バックエンドクラス

| DS-ID | クラス名 | 役割 | SOLID適合 |
|---|---|---|---|
| DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API | DepartmentRouter | 部署名取得 API エンドポイント定義（GET /api/department/by-login-id） | S: 部署 API のみ |
| DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID | DepartmentService | 部署名取得ビジネスロジック。クライアントを注入して None を「不明」に変換する | S: 部署名取得のみ |
| DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION | ReservationRouter | 予約 CRUD API エンドポイント定義 | S: 予約 API のみ |
| DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION | ReservationService | 予約 CRUD・競合チェック・ステータス更新のビジネスロジック | S: 予約業務ロジックのみ |
| DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY | ReservationRepository | reservation テーブルの CRUD データアクセス | S: データ永続化のみ |

**DepartmentService の責務・主要メソッド (DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID):**

| 種別 | 名前 | 説明 |
|---|---|---|
| 属性 | _client | RealDepartmentClient または MockDepartmentClient（FastAPI Depends で注入） |
| メソッド | get_department_name(login_id: str) → str | _client.fetch_department_name_by_login_id(login_id) を呼び出す。None または例外発生時は "不明" を返す |

**ReservationService の責務・主要メソッド (DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION):**

| 種別 | 名前 | 説明 |
|---|---|---|
| メソッド | list_by_equipment(equipment_id: str) → list[Reservation] | 備品IDに紐づく全予約を開始日昇順で返す |
| メソッド | create(equipment_id, user_login_id, start_date, end_date) → Reservation | 重複チェック後に予約を登録する。equipment.status を 'reserved' に更新する（available 時のみ）。重複時は HTTPException(409) |
| メソッド | cancel(reservation_id, requesting_login_id, requesting_role) | 予約者本人または管理者以外は HTTPException(403)。削除後に残予約数を確認し equipment.status を更新する |

**ReservationRepository の主要メソッド (DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY):**

| 種別 | 名前 | 説明 |
|---|---|---|
| メソッド | find_by_equipment_id(equipment_id: str) → list[Reservation] | 備品IDで全予約を取得 |
| メソッド | count_overlapping(equipment_id, start_date, end_date) → int | 期間重複件数をカウント |
| メソッド | create(data: ReservationCreate, user_login_id: str) → Reservation | 予約レコードを作成 |
| メソッド | find_by_id(reservation_id: str) → Optional[Reservation] | 予約IDで1件取得 |
| メソッド | delete(reservation_id: str) | 予約レコードを削除 |
| メソッド | count_by_equipment_id(equipment_id: str) → int | 備品の有効予約件数をカウント |
| メソッド | delete_expired_by_equipment(equipment_id: str, before_date: str) → None | end_date が before_date より前の予約レコードを全て削除する。返却処理時に呼び出す |

### [追加] 新規フロントエンドクラス

| DS-ID | クラス名 | 役割 | SOLID適合 |
|---|---|---|---|
| DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN | ReservationCalendarView | 備品別予約詳細・カレンダー画面コンポーネント。予約一覧の「予約者名（部署）」表示は、各予約の user_login_id に対して DeptStore.fetchDeptName を呼び出して部署名を非同期取得する | S: 予約カレンダー画面のみ |
| DS-CL-RESERVATION-FORM-VIEW-UI-RESERVATION-FORM-SCREEN | ReservationFormView | 予約登録画面コンポーネント | S: 予約登録フォームのみ |
| DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR | ReservationStore（Pinia） | 予約一覧データの状態管理 | S: 予約状態管理のみ |
| DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID | DeptStore（Pinia） | 部署名のキャッシュ管理と非同期取得 | S: 部署名キャッシュのみ |

**DeptStore の主要メソッド (DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID):**
- `fetchDeptName(loginId)` — GET /api/department/by-login-id を呼び出し、結果をキャッシュに保存する。同一 loginId の2回目以降の呼び出しはキャッシュから返す
- `fetchDeptNames(loginIds)` — 複数 loginId を並行呼び出し（Promise.all）して一括取得する

### 更新後のクラス図（追加分）

```mermaid
classDiagram
    class DepartmentRouter {
        +get_dept_name(login_id) DeptNameResponse
    }
    class DepartmentService {
        -_client
        +get_department_name(login_id) str
    }
    class RealDepartmentClient {
        -_engine
        +fetch_department_name_by_login_id(login_id) Optional[str]
    }
    class MockDepartmentClient {
        +fetch_department_name_by_login_id(login_id) Optional[str]
    }
    class ReservationRouter {
        +list_reservations(equipment_id) list
        +create(equipment_id, ReservationCreate) Reservation
        +cancel(reservation_id) Response
    }
    class ReservationService {
        +list_by_equipment(equipment_id) list
        +create(equipment_id, user_login_id, start_date, end_date) Reservation
        +cancel(reservation_id, req_login_id, req_role)
    }
    class ReservationRepository {
        +find_by_equipment_id(id) list
        +count_overlapping(id, start, end) int
        +create(data, user_id) Reservation
        +find_by_id(id) Reservation
        +delete(id)
        +count_by_equipment_id(id) int
    }
    DepartmentRouter --> DepartmentService
    DepartmentRouter --> AuthService
    DepartmentService --> RealDepartmentClient
    DepartmentService --> MockDepartmentClient
    ReservationRouter --> ReservationService
    ReservationRouter --> AuthService
    ReservationService --> ReservationRepository
    ReservationService --> EquipmentRepository
```

### [追加] 新規メッセージ

| DS-ID | メッセージ名 | 内容 |
|---|---|---|
| DS-EV-DEPT-NAME-RESPONSE-FT-DEPT-NAME-API | DeptNameResponse | department_name: str |
| DS-EV-RESERVATION-CREATE-FT-MAKE-RESERVATION | ReservationCreate | start_date: str, end_date: str, user_login_id: Optional[str] |
| DS-EV-RESERVATION-RESPONSE-FT-VIEW-RESERVATION-CALENDAR | ReservationResponse | reservation_id: str, equipment_id: str, user_login_id: str, user_display_name: str, start_date: str, end_date: str |

### [追加] 外部クライアント DI 設計

FastAPI Depends を使い、環境変数 `MOCK_EXTERNAL_DB` の値に応じてクライアントを差し替える。

**DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID の DI ファクトリ（core/external_department.py）:**

| MOCK_EXTERNAL_DB 値 | 返却クライアント |
|---|---|
| "true" | MockDepartmentClient（mock/mock_department_client.py） |
| "false"（または未設定） | RealDepartmentClient（external/neon-department-db/src/department_client.py） |

---

## 6. その他設計（変更分）

### エラーハンドリング設計（追加分）

| DS-ID | HTTP ステータス | 発生条件 | レスポンス内容 |
|---|---|---|---|
| DS-FN-ERROR-409-RESERVATION-CONFLICT-FT-MAKE-RESERVATION | 409 Conflict | 重複する予約期間への予約登録 | {"detail": "指定期間は既に予約されています"} |
| DS-FN-ERROR-403-RESERVATION-CANCEL-FT-CANCEL-RESERVATION | 403 Forbidden | 他の利用者の予約を一般利用者がキャンセル | {"detail": "権限がありません"} |
| DS-FN-ERROR-EXTERNAL-DB-DEPT-EX-FETCH-DEPARTMENT-MASTER | （HTTP ステータスなし） | 外部DB接続失敗・タイムアウト | DepartmentService が "不明" を返す。HTTP 200 で {"department_name": "不明"} を返却。他の操作は継続可能 |

### セキュリティ設計（追加分）

| DS-ID | 設計項目 | 設計内容 |
|---|---|---|
| DS-FN-EXTERNAL-DB-READONLY-NF-EXTERNAL-DB-READONLY | 外部DB書き込み禁止 | external/neon-department-db/src/department_client.py は SELECT のみ実行する。INSERT/UPDATE/DELETE を実行するコードを禁止する |
| DS-FN-EXTERNAL-DB-TIMEOUT-NF-EXTERNAL-DB-TIMEOUT | 外部DB接続タイムアウト | get_external_db_engine() の connect_args={"connect_timeout": 5} で5秒タイムアウトを設定する |
| DS-FN-EXTERNAL-DB-SECRET-EX-FETCH-DEPARTMENT-MASTER | 接続情報保護 | EXTERNAL_DB_URL は .env ファイルにのみ記載する。コードへの直書きを禁止する |

---

## 7. コード設計（変更分）

### ディレクトリ構成（変更分）

変更なし。既存設計 `docs/detail_design.md` セクション7 を参照。追加ファイルは以下の通り。

### [追加] 新規ファイル一覧

#### external/neon-department-db/src/

| ファイル名 | 役割 | DS-ID |
|---|---|---|
| department_client.py（既存・更新） | RealDepartmentClient クラスを追記する（既存の module-level 関数はそのまま維持） | DS-CL-REAL-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER |

#### backend/app/

| ファイル名 | 役割 | DS-ID |
|---|---|---|
| core/external_department.py | 環境変数に応じて RealDepartmentClient / MockDepartmentClient を返す Depends ファクトリ | DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID |
| models/reservation.py | Reservation ORM モデル（reservation テーブル） | DS-SC-RESERVATION-DT-RESERVATION-ENTITY |
| schemas/reservation.py | ReservationCreate / ReservationResponse | DS-EV-RESERVATION-CREATE-FT-MAKE-RESERVATION |
| schemas/department.py | DeptNameResponse | DS-EV-DEPT-NAME-RESPONSE-FT-DEPT-NAME-API |
| repositories/reservation.py | ReservationRepository | DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY |
| services/department_service.py | DepartmentService | DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID |
| services/reservation_service.py | ReservationService | DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION |
| api/department.py | DepartmentRouter（GET /api/department/by-login-id） | DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API |
| api/reservations.py | ReservationRouter（GET・POST /api/equipment/{id}/reservations、DELETE /api/reservations/{id}） | DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION |

#### frontend/src/

| ファイル名 | 役割 | DS-ID |
|---|---|---|
| views/ReservationCalendarView.vue | 備品別予約詳細・カレンダー画面 | DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN |
| views/ReservationFormView.vue | 予約登録画面 | DS-CL-RESERVATION-FORM-VIEW-UI-RESERVATION-FORM-SCREEN |
| stores/reservation.js | ReservationStore（Pinia） | DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR |
| stores/dept.js | DeptStore（Pinia） | DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID |
| api/department.js | 部署名取得 API コール関数 | DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API |
| api/reservations.js | 予約 API コール関数 | DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION |

### [追加] Vue Router ルート追加

| パス | View | 権限ガード |
|---|---|---|
| /equipment/:id/reservations | ReservationCalendarView | 要ログイン（全ロール） |
| /equipment/:id/reservations/new | ReservationFormView | 要ログイン（全ロール） |

### [追加] docker compose 環境変数追加

backend サービスに以下を追加する:

| 変数名 | 説明 |
|---|---|
| EXTERNAL_DB_URL | Neon PostgreSQL 接続文字列（real モード時に必須） |
| MOCK_EXTERNAL_DB | "true" で MockDepartmentClient を使用する。デフォルト "false" |

external/neon-department-db ディレクトリを backend コンテナに `/app/external/neon-department-db` としてマウントする。PYTHONPATH に `/app/external/neon-department-db` を追加する。

---

## 8. テスト設計（変更分）

### [追加] 単体テスト（追加分）

| DS-ID | テスト対象 | 正常系 | 異常系 |
|---|---|---|---|
| DS-FN-TEST-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID | DepartmentService.get_department_name | クライアントが部署名を返す → そのまま返す | クライアントが None を返す → "不明"。クライアントが例外を送出 → "不明" |
| DS-FN-TEST-RESERVATION-CREATE-FT-MAKE-RESERVATION | ReservationService.create | 重複なし → 予約作成成功・equipment.status 更新 | 重複あり → 409。equipment が存在しない → 404 |
| DS-FN-TEST-RESERVATION-CANCEL-FT-CANCEL-RESERVATION | ReservationService.cancel | 本人がキャンセル成功・残予約0件→status=available | 他人がキャンセル → 403。管理者がキャンセル成功。残予約あり → status=reserved |
| DS-FN-TEST-RESERVATION-CONFLICT-NF-RESERVATION-CONFLICT-PREVENTION | ReservationRepository.count_overlapping | 重複なし → 0。前後接触（境界）→ 0 | 1日重複 → 1。完全包含 → 1 |
| DS-FN-TEST-LOAN-RESERVED-FT-LOAN-EQUIPMENT | EquipmentService.loan（更新） | status='reserved' でも貸出成功 | status='loaned' は 409（変更なし） |
| DS-FN-TEST-RETURN-UPDATE-STATUS-FT-RETURN-EQUIPMENT | EquipmentService.return_equipment（更新） | 残予約あり → status='reserved'。残予約なし → status='available'。end_date < 返却日の予約が自動削除される | 既存の404エラーは変更なし |

### [追加] 結合テスト（追加分）

| DS-ID | テスト対象 | 正常系 | 異常系 |
|---|---|---|---|
| DS-FN-TEST-API-DEPT-NAME-FT-DEPT-NAME-API | GET /api/department/by-login-id | ログイン済みで200・部署名返却（モッククライアント） | 未ログイン → 401 |
| DS-FN-TEST-API-RESERVATION-CRUD-FT-MAKE-RESERVATION | GET/POST /api/equipment/{id}/reservations、DELETE /api/reservations/{id} | 予約一覧取得・予約作成・キャンセル成功 | 重複期間 → 409。他人キャンセル → 403。一般利用者が他人のIDで予約作成 → 403 |

---

## 9. 運用設計（変更分）

### [追加] docker compose 変更

backend サービスの環境変数に `EXTERNAL_DB_URL`・`MOCK_EXTERNAL_DB` を追加する。

`.env` に以下を追記する:
```
EXTERNAL_DB_URL=postgresql://user:password@host/db?sslmode=require&channel_binding=require
MOCK_EXTERNAL_DB=false
```

mock モードで起動する場合は `MOCK_EXTERNAL_DB=true` に設定する（EXTERNAL_DB_URL は不要）。

### [追加] 初期化設計への追加

- SQLAlchemy create_all に reservation テーブルの定義を追加する。

### [追加] README.md への追記内容

- `EXTERNAL_DB_URL` の設定方法（real モード時のみ必要）
- `MOCK_EXTERNAL_DB=true` でのローカル起動手順（外部DB不要）

---

## 10. ログ・監視・アラート設計

変更なし。既存設計 `docs/detail_design.md` セクション10 を参照。

---

## 11. E2Eテスト設計（変更分）

### [追加] docker compose への外部DB対応

```yaml
test_playwright:
  image: mcr.microsoft.com/playwright:v1.59.0
  profiles:
    - test
    - mock
    - real
  volumes:
    - ./e2e:/e2e
  working_dir: /e2e
  depends_on:
    - frontend
    - backend
  environment:
    - BASE_URL=http://frontend

backend:
  environment:
    - MOCK_EXTERNAL_DB=${MOCK_EXTERNAL_DB:-true}
    - EXTERNAL_DB_URL=${EXTERNAL_DB_URL:-}
```

プロファイル `mock`（デフォルト CI）: `MOCK_EXTERNAL_DB=true`  
プロファイル `real`（手動実行）: `MOCK_EXTERNAL_DB=false` + `EXTERNAL_DB_URL` 設定済み

### [追加] E2E 実行コマンド

**mock モード（CI 必須）:**
```
MOCK_EXTERNAL_DB=true docker compose run --rm test_playwright sh -c "npm install && npx playwright test"
```

**real モード（手動のみ）:**
```
MOCK_EXTERNAL_DB=false docker compose run --rm test_playwright sh -c "npm install && npx playwright test"
```

### [追加] E2E シナリオ（追加分）

| DS-ID | 対応 RQ-TS | 目的 | 前提条件 | 手順 | 期待結果 | モード |
|---|---|---|---|---|---|---|
| DS-FN-E2E-DEPT-DISPLAY-TS-VERIFY-DEPT-DISPLAY-FROM-EXTERNAL | RQ-TS-VERIFY-DEPT-DISPLAY-FROM-EXTERNAL | 画面即時表示後に非同期で部署名が取得・表示されること | 管理者ログイン済み。login_id が demo_users に存在する利用者が登録済み | 1. 利用者一覧画面を開く 2. 初期表示で部署列が「取得中...」であることを確認 3. 取得完了後の表示を確認 | 2. 画面本体は即時表示される 3.「取得中...」が部署名に置き換わる | mock / real |
| DS-FN-E2E-DEPT-LOAN-TS-VERIFY-DEPT-DISPLAY-IN-LOAN | RQ-TS-VERIFY-DEPT-DISPLAY-IN-LOAN | 貸出登録画面のドロップダウンに部署名が表示されること | 管理者ログイン済み | 1. 在庫備品の「貸出」ボタンを押す 2. 貸出登録画面のドロップダウンを確認 | 「利用者名（部署名）」形式で選択肢が表示される | mock / real |
| DS-FN-E2E-DEPT-EQUIPMENT-LIST-TS-VERIFY-DEPT-DISPLAY-IN-EQUIPMENT-LIST | RQ-TS-VERIFY-DEPT-DISPLAY-IN-EQUIPMENT-LIST | 管理者向け備品一覧の貸出先に部署名が表示されること | 管理者ログイン済み、貸出中備品が存在する | 1. 管理者向け備品一覧を開く | 貸出中備品行に「利用者名（部署名）」が表示される | mock / real |
| DS-FN-E2E-RESERVATION-CREATE-TS-VERIFY-RESERVATION-CREATE | RQ-TS-VERIFY-RESERVATION-CREATE | 一般利用者が備品を期間指定で予約できること | 一般利用者ログイン済み、在庫備品が存在する | 1.「予約状況」ボタンを押す 2. カレンダー画面で「予約する」を押す 3. 開始日・終了日を入力して登録する | カレンダーに予約期間がハイライト表示される。備品一覧のステータスが「予約済み」になる | mock / real |
| DS-FN-E2E-RESERVATION-CONFLICT-TS-VERIFY-RESERVATION-CONFLICT | RQ-TS-VERIFY-RESERVATION-CONFLICT | 重複する期間の予約が拒否されること | 一般利用者ログイン済み、対象備品に 2026-06-01〜2026-06-05 の予約が存在する | 1. 同じ備品に 2026-06-03〜2026-06-07 の期間で予約を試みる | 「指定期間は既に予約されています」が表示され、予約が登録されない | mock / real |
| DS-FN-E2E-RESERVATION-NON-OVERLAP-TS-VERIFY-RESERVATION-NON-OVERLAP | RQ-TS-VERIFY-RESERVATION-NON-OVERLAP | 重複しない期間の複数予約が許可されること | 一般利用者ログイン済み、対象備品に 2026-06-01〜2026-06-05 の予約が存在する | 1. 同じ備品に 2026-06-10〜2026-06-15 の期間で予約を試みる | 予約が正常に登録される。カレンダーに両方の期間がハイライト表示される | mock / real |
| DS-FN-E2E-RESERVATION-CANCEL-TS-VERIFY-RESERVATION-CANCEL | RQ-TS-VERIFY-RESERVATION-CANCEL | 予約者本人が自分の予約をキャンセルできること | 一般利用者ログイン済み、当該利用者の予約が存在する | 1.「予約状況」ボタンを押す 2. 自分の予約行の「キャンセル」ボタンを押す | カレンダーから該当予約が消える。他に予約がなければ備品ステータスが「在庫」になる | mock / real |
| DS-FN-E2E-ADMIN-CANCEL-RESERVATION-TS-VERIFY-ADMIN-CANCEL-OTHERS-RESERVATION | RQ-TS-VERIFY-ADMIN-CANCEL-OTHERS-RESERVATION | 管理者が他利用者の予約をキャンセルできること | 管理者ログイン済み、他の利用者の予約が存在する | 1. 該当備品の「予約状況」ボタンを押す 2. 他の利用者の予約行の「キャンセル」ボタンを押す | 該当予約がカレンダーから消える | mock / real |
| DS-FN-E2E-RESERVATION-TO-LOAN-TS-VERIFY-RESERVATION-TO-LOAN | RQ-TS-VERIFY-RESERVATION-TO-LOAN | 予約済み備品に対して管理者が貸出操作でき、返却時に期間終了済み予約が自動削除されること | 管理者ログイン済み、予約済み状態の備品が存在する | 1. 備品一覧の「貸出」ボタンを押す 2. 貸出登録画面で利用者を選択して登録する 3. 備品を返却する | 2. 備品ステータスが「貸出中」になる 3. end_date が返却日より前の予約が自動削除される。残予約がなければ備品ステータスが「在庫」になる | mock / real |
| DS-FN-E2E-EXTERNAL-DB-FAILURE-TS-VERIFY-EXTERNAL-DB-FAILURE | RQ-TS-VERIFY-EXTERNAL-DB-FAILURE | 外部DB接続失敗時に部署名が「不明」と表示されること | 外部DBが接続不可の状態（MOCK_EXTERNAL_DB=false かつ EXTERNAL_DB_URL に無効な値） | 1. 利用者一覧画面を開く | 部署名欄に「不明」が表示される。他の画面表示・操作は継続可能 | real |

### [追加] E2E ファイル追加

| ファイル名 | 役割 | DS-ID |
|---|---|---|
| e2e/tests/reservations.spec.js | 予約 CRUD・競合チェック・キャンセル E2E テスト | DS-FN-E2E-RESERVATION-CREATE-TS-VERIFY-RESERVATION-CREATE |
| e2e/tests/department.spec.js | 部署名非同期表示 E2E テスト | DS-FN-E2E-DEPT-DISPLAY-TS-VERIFY-DEPT-DISPLAY-FROM-EXTERNAL |

### [追加] E2E 運用設計の変更

- 外部モックは `external/neon-department-db/mock/` を正本とし、`e2e/external/neon-department-db/mock` からシンボリックリンクで参照する。シンボリックリンクは Git 管理下に置く
- CI 必須ゴールは `mock` モード E2E 全件通過（`MOCK_EXTERNAL_DB=true`）
- `real` モード E2E は手動実行のみ必須

---

## 12. 削除可能な設計要素の確認（変更分）

| 削除した設計要素 | 理由 |
|---|---|
| 部署一覧取得 API（全件取得） | RQ-FT-SELECT-DEPARTMENT が削除されたため不要。ログインIDによる1件取得のみで要件を満たす |
| 利用者フォームへの部署選択フィールド | 外部DB動的取得に変更したため不要 |
| 予約更新（PATCH）API | 修正はキャンセル→再登録で対応するため Update は設計しない |
