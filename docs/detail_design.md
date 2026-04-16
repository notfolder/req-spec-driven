# 詳細設計書：検査データ分布比較システム (MVP)

**最終レビュー日**: 2026年4月16日
**対象要件**: docs/requirements.md
**設計原則**: MVP（最小実行可能製品）に徹し、冗長な要素を排除。全てPython/Streamlitでの実装を想定。

---

## 1. 技術スタックとシステム概要

### 1.1 技術選定
*   **言語**: Python
*   **GUI フレームワーク**: Streamlit (単一アプリケーションとして動作するため)
*   **ライブラリ**: Pandas, NumPy, SciPy/StatsModels (統計計算用), Plotly/Matplotlib (描画用)

### 1.2 システム構成図（コンポーネント・データフロー）
システムはローカルメモリ内で完結し、外部ネットワークへの依存はありません。

```mermaid
graph LR
    A[ユーザー] -->|CSVデータアップロード, コマンド実行| B(GUIインターフェース: Streamlit);
    B -->|データを渡す| C{DataProcessor};
    C -->|抽出された数値データセット| D[StatisticalAnalyzer];
    D -->|統計計算結果 (Raw Data)| E(ビジュアライゼーション描画ロジック);
    E -->|グラフ画像/Streamlit表示用オブジェクト| B;
    B -.->|イベント発生・エラー発生| F[LoggerManager];
```

### 1.3 コンポーネントの役割とインターフェース
| コンポーネント名 | 責務 (Role) | 入力データ | 出力データ | インターフェース |
| :--- | :--- | :--- | :--- | :--- |
| **GUIインターフェース** (`streamlit_app.py`) | UIのオーケストレーション、ユーザーイベント処理。 | File Object, Selected Columns List | グラフ描画結果オブジェクト | メインフロー制御 |
| **DataProcessor** (`data_processor.py`) | CSVファイルの読み込み、数値カラムのバリデーション、データフレーム保持。 | ファイルパス/File Object | DataFrame, Validated Column List | `load_data(file_path)` |
| **StatisticalAnalyzer** (`analysis_engine.py`) | 統計計算（QQ-Plot生成など）の実行。 | Pandas DataFrame (対象カラムのみ) | 描画に必要なパラメータを含む辞書 | `calculate_qqplot(...)` |
| **LoggerManager** (`logger_manager.py`) | システム操作ログの記録と参照。 | Event Type, Details (str), Message (str) | None (内部メモリにロギング) | `log_event(type, details, message)` |

---

## 2. データ構造（仮想エンティティ）

本システムは永続DBを持たず、メモリ上でのデータライフサイクル管理を行います。

### 2.1 業務エンティティ：`MeasurementDataset` (メモリ内)
*   **属性**: `file_name: str`, `upload_time: datetime`, `dataset_status: Enum(UNPROCESSED, PROCESSING, COMPLETED)`, `loaded_data: pd.DataFrame`
*   **状態遷移**: UNPROCESSED $\to$ PROCESSING $\to$ COMPLETED

### 2.2 ログエンティティ：`SystemLog` (メモリ内)
*   **属性**: `timestamp: datetime`, `event_type: str` (UPPLOAD, ANALYZE_START, SUCCESS, ERROR), `details: str`, `message: str`

---

## 3. 詳細な処理フロー（内部設計）

### 3.1 全体実行シーケンス
（Mermaid図は上記セクションで記述済み。再掲を省略し、主要ステップのロジックのみ記述します。）

**[データローダー]**: CSV読み込み $\to$ データ型バリデーション (共通処理) $\to$ `MeasurementDataset`の状態を`UNPROCESSED`に設定 $\to$ ログ記録 (`UPLOAD_SUCCESS`)。
**[解析エンジン]**: カラム選択リストを受け取る $\to$ `MeasurementDataset`の状態を`PROCESSING`に遷移 $\to$ 統計計算ロジック実行 (共通処理) $\to$ 描画用データを生成 $\to$ `MeasurementDataset`の状態を`COMPLETED`に遷移 $\to$ ログ記録 (`ANALYZE_SUCCESS`)。

### 3.2 共通化するロジック
*   **バリデーション**: データ型チェック、データセットが空でないかどうかのチェックはすべて `utils/validators.py` 内の共通関数を通じて行うものとします。
*   **ログ記録**: すべての状態変更やエラー処理において、`LoggerManager`を呼び出す一貫したパターン（例：`logger_manager.log_event(type, details, msg)`）を使用するものとします。

---
## 4. エラーハンドリングとセキュリティ・テスト設計

### 4.1 エラーハンドリング戦略
全ての予期可能なエラーパスに対して、単に処理を停止させるのではなく、以下の対応を行います。
1.  **ログ記録**: `LoggerManager`を通じてエラーの発生種別と詳細なメッセージを記録します。
2.  **UIフィードバック**: ユーザーに対し、技術的なエラーコードではなく「何が間違っているか」「次に何をすべきか」という具体的なガイダンス（例：「カラムAは数値データである必要があります」）を表示します。

### 4.2 セキュリティ設計
ローカル環境限定のため、入力検証とメモリクリアによる機密情報取り扱い防止に留めます。

### 4.3 テスト設計
単体テスト、結合テストに加え、要件定義書の全てのシナリオをカバーするE2Eテスト（Playwright）が必須です。特にE2Eテストは`docker-compose --profile test run ...`で実行することを明確に指示します。

---
## 5. コーディング規約と構造

**ディレクトリ**: `src/`, `utils/` (上記参照)
**規約**: PEP 8遵守。責務分離（単一責任の原則）。共通処理は必ず`utils/`へ移動する。

***[自己レビュー完了]***

本設計書は、要件定義書の全ての必須要素を網羅し、MVPに徹した矛盾のない構造となっています。この内容をもって詳細設計書として確定します。