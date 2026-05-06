# 実装タスク一覧 — 部署マスタ連携 & 備品予約機能追加

作成日: 2026-05-06  
対応変更設計書: `.history/20260506-add-department-and-reservation/change_detail_design.md`

---

## タスク 1: 外部DB連携クライアント更新（RealDepartmentClient 追加）

**対応設計ID**: DS-CL-REAL-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER

**作業内容**:
- `external/neon-department-db/src/department_client.py` に `RealDepartmentClient` クラスを追記する
  - `__init__()`: `get_external_db_engine()` でエンジンを生成して `self._engine` に保持する
  - `fetch_department_name_by_login_id(login_id: str) -> Optional[str]`: `fetch_department_name_by_login_id(self._engine, login_id)` を呼び出して返す
- 既存の module-level 関数（`get_external_db_engine`・`fetch_department_name_by_login_id`）はそのまま維持する

**完了条件**:
- `RealDepartmentClient` と `MockDepartmentClient` の `fetch_department_name_by_login_id` シグネチャが一致している
- `isdd-traceable-coding` 準拠コメントが付与されている

**バリデーション**:
- `external/neon-department-db/tests/unit/test_department_client.py` の全テスト（12件）が PASS する
- `external/neon-department-db/tests/unit/test_mock_department_client.py` の全テスト（15件）が PASS する

---

## タスク 2: DI ファクトリ実装（core/external_department.py）

**対応設計ID**: DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID

**作業内容**:
- `backend/app/core/external_department.py` を新規作成する
  - 環境変数 `MOCK_EXTERNAL_DB` が `"true"` の場合: `MockDepartmentClient` を返す
  - それ以外の場合: `RealDepartmentClient` を返す
  - FastAPI `Depends` で利用できる形式のファクトリ関数として実装する
- `isdd-traceable-coding` 準拠コメントを付与する

**完了条件**:
- `MOCK_EXTERNAL_DB=true` 設定時に `MockDepartmentClient` が返される
- `MOCK_EXTERNAL_DB=false`（または未設定）時に `RealDepartmentClient` が返される

**バリデーション**:
- 結合テスト（タスク 10）の `GET /api/department/by-login-id` テストが PASS する

---

## タスク 3: バックエンド — スキーマ・ORM モデル追加

**対応設計ID**: DS-SC-RESERVATION-DT-RESERVATION-ENTITY, DS-EV-RESERVATION-CREATE-FT-MAKE-RESERVATION, DS-EV-RESERVATION-RESPONSE-FT-VIEW-RESERVATION-CALENDAR, DS-EV-DEPT-NAME-RESPONSE-FT-DEPT-NAME-API

**作業内容**:
- `backend/app/models/reservation.py` を新規作成する
  - `Reservation` ORM モデル（`reservation_id` UUID PK, `equipment_id` FK ON DELETE CASCADE, `user_login_id` FK, `start_date`, `end_date`）
- `backend/app/schemas/reservation.py` を新規作成する
  - `ReservationCreate`（`start_date`, `end_date`, `user_login_id: Optional[str]`）
  - `ReservationResponse`（`reservation_id`, `equipment_id`, `user_login_id`, `user_display_name`, `start_date`, `end_date`）
- `backend/app/schemas/department.py` を新規作成する
  - `DeptNameResponse`（`department_name: str`）
- `isdd-traceable-coding` 準拠コメントを全クラスに付与する

**完了条件**:
- 各ファイルが構文エラーなく import できる
- `reservation_id` が UUID 形式で自動生成される設計になっている
- `equipment_id` FK に `ON DELETE CASCADE` が設定されている

**バリデーション**:
- `python -c "from app.models.reservation import Reservation; from app.schemas.reservation import ReservationCreate, ReservationResponse; from app.schemas.department import DeptNameResponse"` がエラーなく実行できる

---

## タスク 4: バックエンド — DB マイグレーション（reservation テーブル追加 + equipment.status 拡張）

**対応設計ID**: DS-SC-RESERVATION-DT-RESERVATION-ENTITY, DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY

**作業内容**:
- `backend/app/` の SQLAlchemy `create_all` 実行箇所（`main.py` または `database.py`）に `Reservation` モデルを import して reservation テーブルを作成対象に追加する
- equipment テーブルの `status` カラム許容値を `'available'`・`'reserved'`・`'loaned'` の3値として扱う（SQLite は CHECK 制約を後付けできないため、アプリ層で管理する。既存データの `status` 値はそのまま有効）

**完了条件**:
- アプリ起動時に `reservation` テーブルが自動作成される
- 既存テーブル（`equipment`・`user`・`loan_state`）が破壊されない

**バリデーション**:
- アプリ起動後に `sqlite3 data/app.db ".tables"` で `reservation` テーブルが確認できる
- `.schema reservation` でカラム定義・FK 制約が設計通りであることを確認する

---

## タスク 5: バックエンド — ReservationRepository 実装

**対応設計ID**: DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY

**作業内容**:
- `backend/app/repositories/reservation.py` を新規作成する
- 以下のメソッドを実装する:
  - `find_by_equipment_id(equipment_id: str) -> list[Reservation]` — 開始日昇順
  - `count_overlapping(equipment_id: str, start_date: str, end_date: str) -> int` — 日付重複件数
  - `create(data: ReservationCreate, user_login_id: str) -> Reservation` — UUID 自動生成
  - `find_by_id(reservation_id: str) -> Optional[Reservation]`
  - `delete(reservation_id: str)`
  - `count_by_equipment_id(equipment_id: str) -> int`
- `isdd-traceable-coding` 準拠コメントを付与する

**完了条件**:
- 全メソッドが SQLite で正常動作する
- `count_overlapping` が境界値（前後接触）を重複として扱わない（`start_date < req_end AND end_date > req_start` の条件）

**バリデーション**:
- タスク 7 の `ReservationRepository.count_overlapping` 単体テスト（境界値テスト含む）が PASS する

---

## タスク 6: バックエンド — DepartmentService 実装

**対応設計ID**: DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID

**作業内容**:
- `backend/app/services/department_service.py` を新規作成する
- `DepartmentService` クラスを実装する:
  - `__init__(client)`: クライアント（Real/Mock）を受け取る
  - `get_department_name(login_id: str) -> str`: `_client.fetch_department_name_by_login_id(login_id)` を呼び出す。`None` または例外発生時は `"不明"` を返す
- `isdd-traceable-coding` 準拠コメントを付与する

**完了条件**:
- クライアントが `None` を返す場合に `"不明"` が返る
- クライアントが例外を送出する場合に `"不明"` が返る（例外を上位に伝播しない）

**バリデーション**:
- タスク 7 の `DepartmentService.get_department_name` 単体テストが PASS する

---

## タスク 7: バックエンド — ReservationService 実装

**対応設計ID**: DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION, DS-FN-VALIDATE-RESERVATION-CONFLICT-NF-RESERVATION-CONFLICT-PREVENTION, DS-FN-VALIDATE-LOAN-AVAILABLE-RESERVED-FT-LOAN-EQUIPMENT, DS-FN-VALIDATE-RESERVATION-CANCEL-FT-CANCEL-RESERVATION

**作業内容**:
- `backend/app/services/reservation_service.py` を新規作成する
- `ReservationService` クラスを実装する:
  - `list_by_equipment(equipment_id: str)` — `ReservationRepository.find_by_equipment_id` を呼び出す
  - `create(equipment_id, user_login_id, start_date, end_date)`:
    1. equipment 存在確認 → なし: `HTTPException(404)`
    2. SQLite トランザクション内で `count_overlapping` → 1以上: `HTTPException(409, "指定期間は既に予約されています")`
    3. `reservation` レコード作成
    4. `equipment.status == 'available'` の場合のみ `'reserved'` に更新
    5. コミット
  - `cancel(reservation_id, requesting_login_id, requesting_role)`:
    1. reservation 取得 → なし: `HTTPException(404)`
    2. 本人以外かつ管理者以外: `HTTPException(403, "権限がありません")`
    3. SQLite トランザクション内で `reservation` 削除
    4. `count_by_equipment_id` が 0 かつ `equipment.status != 'loaned'` の場合に `status = 'available'` に更新
    5. コミット
- 既存の `EquipmentService.loan` を更新: `status in ('available', 'reserved')` の場合に貸出を許可する（既存の `'available'` のみから拡張）
- 既存の `EquipmentService.return_equipment` を更新: `loan_state` 削除後に `ReservationRepository.delete_expired_by_equipment(equipment_id, 返却日)` を呼び出して期間終了済み予約を削除する。その後 `count_by_equipment_id` を確認し、1以上なら `'reserved'`、0なら `'available'` に更新する
- `isdd-traceable-coding` 準拠コメントを付与する

**完了条件**:
- 予約作成・キャンセル・競合チェック・ステータス遷移規則が設計書通り実装されている
- 貸出・返却のステータス更新ロジックが3値対応になっている
- トランザクション境界が設計書通りである（DS-FN-TRANSACTION-RESERVATION, DS-FN-TRANSACTION-CANCEL-RESERVATION, DS-FN-TRANSACTION-RETURN-UPDATE）

**バリデーション**:
- 以下の単体テストが全て PASS する:
  - `DS-FN-TEST-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID`（DepartmentService）
  - `DS-FN-TEST-RESERVATION-CREATE-FT-MAKE-RESERVATION`（ReservationService.create）
  - `DS-FN-TEST-RESERVATION-CANCEL-FT-CANCEL-RESERVATION`（ReservationService.cancel）
  - `DS-FN-TEST-RESERVATION-CONFLICT-NF-RESERVATION-CONFLICT-PREVENTION`（ReservationRepository.count_overlapping）
  - `DS-FN-TEST-LOAN-RESERVED-FT-LOAN-EQUIPMENT`（EquipmentService.loan 更新）
  - `DS-FN-TEST-RETURN-UPDATE-STATUS-FT-RETURN-EQUIPMENT`（EquipmentService.return_equipment 更新）

---

## タスク 8: バックエンド — API ルーター実装

**対応設計ID**: DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API, DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION, DS-IF-DEPT-NAME-BY-LOGIN-ID-FT-DEPT-NAME-API, DS-IF-RESERVATION-LIST-FT-VIEW-RESERVATION-CALENDAR, DS-IF-RESERVATION-CREATE-FT-MAKE-RESERVATION, DS-IF-RESERVATION-DELETE-FT-CANCEL-RESERVATION

**作業内容**:
- `backend/app/api/department.py` を新規作成する:
  - `GET /api/department/by-login-id?login_id=xxx`（要ログイン）→ `DeptNameResponse`
  - 未ログイン: 401
- `backend/app/api/reservations.py` を新規作成する:
  - `GET /api/equipment/{id}/reservations`（要ログイン）→ `ReservationResponse[]`
  - `POST /api/equipment/{id}/reservations`（要ログイン）→ `ReservationResponse`（201）
  - `DELETE /api/reservations/{reservation_id}`（要ログイン）→ 204
- 各ルーターを `backend/app/main.py` に登録する
- `isdd-traceable-coding` 準拠コメントを付与する

**完了条件**:
- 全エンドポイントが設計書のスキーマ通りに実装されている
- 一般利用者が `POST /api/equipment/{id}/reservations` で `user_login_id` を指定した場合に 403 を返す
- 管理者が `user_login_id` を指定して予約登録できる

**バリデーション**:
- タスク 10 の結合テスト（`DS-FN-TEST-API-DEPT-NAME-FT-DEPT-NAME-API`・`DS-FN-TEST-API-RESERVATION-CRUD-FT-MAKE-RESERVATION`）が全て PASS する

---

## タスク 9: バックエンド — docker compose 環境変数・マウント追加

**対応設計ID**: DS-MD-EXTERNAL-DEPT-DB-EX-FETCH-DEPARTMENT-MASTER（セクション7）

**作業内容**:
- `docker-compose.yml` の `backend` サービスに以下を追加する:
  - 環境変数: `EXTERNAL_DB_URL=${EXTERNAL_DB_URL:-}`・`MOCK_EXTERNAL_DB=${MOCK_EXTERNAL_DB:-true}`
  - ボリューム: `./external/neon-department-db:/app/external/neon-department-db`
  - `PYTHONPATH` に `/app/external/neon-department-db` を追加する
- `.env.example` に `EXTERNAL_DB_URL` と `MOCK_EXTERNAL_DB` の説明コメントと変数名を追記する
- `README.md` に `EXTERNAL_DB_URL` の設定方法と `MOCK_EXTERNAL_DB=true` でのローカル起動手順を追記する

**完了条件**:
- `MOCK_EXTERNAL_DB=true docker compose up backend` で外部DB不要で起動できる
- `.env.example` に認証情報の値が含まれていない（変数名とダミー値のみ）

**バリデーション**:
- `docker compose config` でボリューム・環境変数の設定が正しく展開されることを確認する

---

## タスク 10: バックエンド — 単体テスト・結合テスト追加

**対応設計ID**: DS-FN-TEST-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID, DS-FN-TEST-RESERVATION-CREATE-FT-MAKE-RESERVATION, DS-FN-TEST-RESERVATION-CANCEL-FT-CANCEL-RESERVATION, DS-FN-TEST-RESERVATION-CONFLICT-NF-RESERVATION-CONFLICT-PREVENTION, DS-FN-TEST-LOAN-RESERVED-FT-LOAN-EQUIPMENT, DS-FN-TEST-RETURN-UPDATE-STATUS-FT-RETURN-EQUIPMENT, DS-FN-TEST-API-DEPT-NAME-FT-DEPT-NAME-API, DS-FN-TEST-API-RESERVATION-CRUD-FT-MAKE-RESERVATION

**作業内容**:
- 以下の単体テストを追加する（SQLite または mock 使用）:
  - `DepartmentService.get_department_name`: 正常・None返却・例外時に "不明" を返すことを検証
  - `ReservationService.create`: 重複なし成功・409競合・404 not found
  - `ReservationService.cancel`: 本人キャンセル・管理者キャンセル・403（他人）・残予約あり/なしでのstatus更新
  - `ReservationRepository.count_overlapping`: 重複なし・境界値（前後接触）→0・1日重複→1・完全包含→1
  - `EquipmentService.loan`（更新）: `status='reserved'` でも貸出成功
  - `EquipmentService.return_equipment`（更新）: 残予約あり→`'reserved'`・残予約なし→`'available'`
- 以下の結合テストを追加する（FastAPI TestClient 使用）:
  - `GET /api/department/by-login-id`: ログイン済み200・未ログイン401
  - `POST /api/equipment/{id}/reservations`: 成功201・重複409・一般利用者が他人IDで登録→403
  - `GET /api/equipment/{id}/reservations`: 成功200・未ログイン401
  - `DELETE /api/reservations/{id}`: 成功204・他人が削除→403・存在しない→404

**完了条件**:
- 全テストが PASS する
- 異常系（409・403・404・401）が網羅されている

**バリデーション**:
- `pytest backend/tests/ -v` が全 PASS する

---

## タスク 11: フロントエンド — api 層追加（department.js・reservations.js）

**対応設計ID**: DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API, DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION

**作業内容**:
- `frontend/src/api/department.js` を新規作成する:
  - `fetchDeptName(loginId)`: `GET /api/department/by-login-id?login_id={loginId}` を呼び出し `department_name` を返す
- `frontend/src/api/reservations.js` を新規作成する:
  - `listReservations(equipmentId)`: `GET /api/equipment/{id}/reservations`
  - `createReservation(equipmentId, data)`: `POST /api/equipment/{id}/reservations`
  - `cancelReservation(reservationId)`: `DELETE /api/reservations/{reservationId}`

**完了条件**:
- 各関数が正しいエンドポイントを呼び出す
- エラーレスポンス（409・403・404）を呼び出し元に伝播する

**バリデーション**:
- タスク 13 のフロントエンド E2E テストで部署名取得・予約 CRUD の通信が正常に動作することを確認する

---

## タスク 12: フロントエンド — Pinia ストア追加（dept.js・reservation.js）

**対応設計ID**: DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID, DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR

**作業内容**:
- `frontend/src/stores/dept.js` を新規作成する（DeptStore）:
  - `fetchDeptName(loginId)`: キャッシュが存在する場合はキャッシュから返す。なければ `api/department.js` を呼び出し結果をキャッシュに保存する
  - `fetchDeptNames(loginIds)`: `Promise.all` で並行取得する
  - キャッシュは `Map<loginId, deptName>` 形式で保持する
- `frontend/src/stores/reservation.js` を新規作成する（ReservationStore）:
  - `reservations`: 現在表示中の備品の予約一覧
  - `fetchReservations(equipmentId)`: `api/reservations.js` を呼び出して `reservations` を更新する
  - `addReservation(equipmentId, data)`: 予約登録後に `reservations` を更新する
  - `removeReservation(reservationId)`: 予約削除後に `reservations` を更新する

**完了条件**:
- DeptStore が同一 loginId への重複 API 呼び出しを防ぐ（キャッシュ機能）
- ReservationStore の CRUD 操作後に UI が自動更新される

**バリデーション**:
- タスク 13・14 のフロントエンドテスト・E2E テストで動作を確認する

---

## タスク 13: フロントエンド — 既存画面更新（4 画面）

**対応設計ID**: DS-CL-USER-LIST-VIEW-UI-BORROWER-LIST-SCREEN, DS-CL-LOAN-FORM-VIEW-UI-LOAN-FORM-SCREEN, DS-CL-ADMIN-EQUIPMENT-LIST-VIEW-UI-ADMIN-EQUIPMENT-LIST-SCREEN, DS-CL-GENERAL-EQUIPMENT-LIST-VIEW-UI-GENERAL-EQUIPMENT-LIST-SCREEN

**作業内容**:
- `UserListView.vue`: 部署列を追加する。画面描画後に `DeptStore.fetchDeptNames` で全利用者の部署名を並行取得する。取得前は「取得中...」、取得失敗・照合不一致は「不明」を表示する
- `LoanFormView.vue`: 貸出先ドロップダウンの選択肢を「利用者名（部署名）」形式に変更する。部署は画面表示後に `DeptStore.fetchDeptName` で非同期取得する。取得前は「利用者名（取得中...）」を表示する
- `AdminEquipmentListView.vue`:
  - 貸出先表示を「利用者名（部署名）」形式に変更する（部署は非同期取得）
  - `status='reserved'` の場合に「予約済み」を表示する
  - 「予約状況」ボタンを追加する（`/equipment/:id/reservations` へ遷移）
  - 「貸出」ボタンを `status in ('available', 'reserved')` の場合に表示する
- `GeneralEquipmentListView.vue`:
  - `status='reserved'` の場合に「予約済み」を表示する
  - 「予約状況」ボタンを追加する（`/equipment/:id/reservations` へ遷移）

**完了条件**:
- 全4画面が AA モックアップ通りのレイアウトになっている
- 「取得中...」→部署名の遷移が画面上で確認できる

**バリデーション**:
- 手動またはブラウザ確認で「取得中...」→部署名への非同期切り替えを確認する
- タスク 15 の E2E テスト（`DS-FN-E2E-DEPT-DISPLAY-TS-VERIFY-DEPT-DISPLAY-FROM-EXTERNAL` 等）が PASS する

---

## タスク 14: フロントエンド — 新規画面追加（ReservationCalendarView・ReservationFormView）

**対応設計ID**: DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN, DS-CL-RESERVATION-FORM-VIEW-UI-RESERVATION-FORM-SCREEN

**作業内容**:
- `frontend/src/views/ReservationCalendarView.vue` を新規作成する:
  - 備品情報（ID・名称・ステータス）を表示する
  - `ReservationStore.reservations` で予約一覧を表形式で表示する（予約者名・部署・開始日・終了日・キャンセルボタン）
  - カレンダーで予約済み期間をハイライト表示する
  - 「予約する」ボタンを常時表示する（`/equipment/:id/reservations/new` へ遷移）
  - 「キャンセル」ボタンは予約者本人の行のみ表示する（管理者は全行に表示）
- `frontend/src/views/ReservationFormView.vue` を新規作成する:
  - 備品ID・名称を表示する
  - 開始日・終了日の入力フォームを提供する（必須バリデーション）
  - 管理者のみ予約者を変更できるドロップダウンを表示する
  - 重複エラー時に「指定期間は既に予約されています」を表示する
  - 登録成功後に `ReservationCalendarView` へ戻る
- Vue Router に以下を追加する（`frontend/src/router/index.js`）:
  - `/equipment/:id/reservations` → `ReservationCalendarView`（要ログイン）
  - `/equipment/:id/reservations/new` → `ReservationFormView`（要ログイン）

**完了条件**:
- 両画面が AA モックアップ通りのレイアウトになっている
- 予約登録・キャンセル後に `ReservationCalendarView` が自動更新される

**バリデーション**:
- タスク 15 の E2E テスト（予約 CRUD 6シナリオ）が PASS する

---

## タスク 15: E2E テスト追加

**対応設計ID**: DS-FN-E2E-DEPT-DISPLAY-TS-VERIFY-DEPT-DISPLAY-FROM-EXTERNAL 〜 DS-FN-E2E-EXTERNAL-DB-FAILURE-TS-VERIFY-EXTERNAL-DB-FAILURE（10シナリオ）

**作業内容**:
- `e2e/tests/department.spec.js` を新規作成する:
  - `DS-FN-E2E-DEPT-DISPLAY-TS-VERIFY-DEPT-DISPLAY-FROM-EXTERNAL`: 「取得中...」→部署名の非同期切り替えを検証
  - `DS-FN-E2E-DEPT-LOAN-TS-VERIFY-DEPT-DISPLAY-IN-LOAN`: 貸出登録画面の「利用者名（部署名）」形式を検証
  - `DS-FN-E2E-DEPT-EQUIPMENT-LIST-TS-VERIFY-DEPT-DISPLAY-IN-EQUIPMENT-LIST`: 管理者向け備品一覧の部署表示を検証
  - `DS-FN-E2E-RESERVATION-TO-LOAN-TS-VERIFY-RESERVATION-TO-LOAN`: 予約済み備品の貸出操作を検証
  - `DS-FN-E2E-EXTERNAL-DB-FAILURE-TS-VERIFY-EXTERNAL-DB-FAILURE`: 外部DB接続失敗時の「不明」表示を検証（real モードのみ）
- `e2e/tests/reservations.spec.js` を新規作成する:
  - `DS-FN-E2E-RESERVATION-CREATE-TS-VERIFY-RESERVATION-CREATE`: 予約登録・ステータス変化を検証
  - `DS-FN-E2E-RESERVATION-CONFLICT-TS-VERIFY-RESERVATION-CONFLICT`: 重複予約拒否を検証
  - `DS-FN-E2E-RESERVATION-NON-OVERLAP-TS-VERIFY-RESERVATION-NON-OVERLAP`: 非重複期間の複数予約を検証
  - `DS-FN-E2E-RESERVATION-CANCEL-TS-VERIFY-RESERVATION-CANCEL`: 本人によるキャンセルを検証
  - `DS-FN-E2E-ADMIN-CANCEL-RESERVATION-TS-VERIFY-ADMIN-CANCEL-OTHERS-RESERVATION`: 管理者による他者予約キャンセルを検証
- mock モードでの symlink を設定する: `e2e/external/neon-department-db/mock` → `../../external/neon-department-db/mock`（Git 管理下）

**完了条件**:
- mock モード（`MOCK_EXTERNAL_DB=true`）での全 E2E テスト（9シナリオ）が PASS する
- `real` モードシナリオ（`DS-FN-E2E-EXTERNAL-DB-FAILURE-TS-VERIFY-EXTERNAL-DB-FAILURE`）は手動実行で PASS する

**バリデーション**:
```
MOCK_EXTERNAL_DB=true docker compose run --rm test_playwright sh -c "npm install && npx playwright test"
```
が全件 PASS する。

---

## タスク 16: 全体確認

**作業内容**:
- 以下の全テストスイートを実行し、全件 PASS を確認する:
  - `external/neon-department-db/` の全テスト（27件：単体12+15）
  - `backend/tests/` の全テスト（既存 + タスク10で追加した単体・結合テスト）
  - `MOCK_EXTERNAL_DB=true` での mock モード E2E（9シナリオ）
- 以下を手動で確認する:
  - 管理者ログイン → 利用者一覧で「取得中...」→部署名切り替え
  - 貸出登録画面のドロップダウンに「利用者名（部署名）」形式で選択肢が表示される
  - 予約登録 → カレンダーハイライト → ステータス「予約済み」
  - 重複期間の予約登録で「指定期間は既に予約されています」が表示される
  - 予約キャンセル後にステータスが「在庫」に戻る
  - 予約済み備品への貸出操作が成功する
- 既存機能のリグレッション確認:
  - ログイン・ログアウト
  - 備品登録・削除・一覧表示
  - 貸出・返却操作（status='available' からの操作）
  - 利用者管理 CRUD

**完了条件**:
- 全テスト PASS
- 手動確認項目が全て設計書の AA モックアップ通りに動作する
- 既存機能にリグレッションがない

---

## タスク 17: ドキュメント反映（必須・最終タスク）

⚠️ **このタスクは既存ファイルを上書きする。実行前に変更内容の完全性を必ず確認すること。**

**作業内容**:
- `docs/requirements.md` に `.history/20260506-add-department-and-reservation/change_requirements.md` の変更内容を反映する
  - `[追加]` 要件を既存の該当セクションに統合する
  - `deprecated` マークされた要件を `docs/requirements.md` から削除する
  - CRUDテーブル・RQ-BK 対応表を更新後の全エンティティ分で更新する
- `docs/detail_design.md` に `.history/20260506-add-department-and-reservation/change_detail_design.md` の変更内容を反映する
  - `[追加]` 設計要素を既存の該当セクションに統合する
  - `deprecated` 設計要素を削除する
  - システム構成図・クラス図・ER図・CRUDテーブル・API一覧を更新後の全要素で更新する

**完了条件（反映内容の完全性確認条件）**:
1. `docs/requirements.md` に全ての `[追加]` 要件（`RQ-FT-FETCH-DEPT-BY-LOGIN-ID`・`RQ-FT-DEPT-NAME-API`・`RQ-FT-VIEW-RESERVATION-CALENDAR`・`RQ-FT-MAKE-RESERVATION`・`RQ-FT-CANCEL-RESERVATION` 等）が反映されている
2. `docs/requirements.md` から `deprecated` 要件（`RQ-EX-NO-EXTERNAL-INTEGRATION`・`RQ-DT-NO-EXTERNAL-DB`・`RQ-FT-SELECT-DEPARTMENT` 等）が削除されている
3. `docs/detail_design.md` のシステム構成図が Neon PostgreSQL を含む更新後の図に差し替えられている
4. `docs/detail_design.md` の ER 図に `reservation` テーブルが追加されている
5. `docs/detail_design.md` のクラス設計に全ての新規クラス（`RealDepartmentClient`・`DepartmentService`・`ReservationService`・`ReservationRepository` 等）が追加されている
6. `docs/detail_design.md` の API 一覧に全ての新規エンドポイント（4件）が追加されている
7. `docs/detail_design.md` から `deprecated` 設計要素が削除されている
8. `change_requirements.md` と `change_detail_design.md` の内容が全て反映されており、抜け漏れが存在しない

**⚠️ 注意**: `docs/requirements.md` と `docs/detail_design.md` は上書きされる。反映前にバックアップを取るか、git commit で現状を保存してから実行すること。
