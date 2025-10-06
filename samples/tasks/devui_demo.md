# TASK-006: DevUI を使った開発者向けデモ

- `id`: TASK-006
- `title`: DevUI を使った開発者向けデモ
- `milestone`: M1
- `priority`: P1
- `category`: dx
- `status`: review

## 概要
Microsoft Agent Framework の DevUI を用いて、ブラウザからエージェント/ワークフローを対話実行・デバッグできる最小デモを提供します。ディレクトリ探索（CLI）とプログラム登録（`serve(entities=[...])`）の両起動パターンをカバーします。

## Deliverables
- path: `samples/devui/README.md`（前提・起動方法・トラブルシュート）
- path: `samples/devui/agents/weather_agent/`（`agent` を `__init__.py` でエクスポート）
- path: `samples/devui/main.py`（`serve(entities=[agent])` で DevUI を起動）

## Acceptance Criteria
- `devui ./samples/devui/agents --port 8080` で WeatherAgent が検出され、チャット実行が可能。
- `python samples/devui/main.py` でプログラム起動し、`http://localhost:8080` が自動で開く（`auto_open`）。
- README に以下が記載されている：
  - 必要要件（Python/uv または pip、`az login` もしくは API Key）。
  - `.env` の設定例（Azure OpenAI または互換エンドポイント）。
  - CLI 起動（ディレクトリ探索）とプログラム起動（インメモリ登録）の手順。
  - トレーシングの有効化（例：`devui ./... --tracing framework`）。

## 実装メモ
- 依存: `agent-framework-devui`（リポジトリ内のワークスペースに含まれる）。
- 認証: 既存サンプルと同様に Azure CLI 認証（`az login`）または API キー（`.env`）。
- エージェント作成は `AzureOpenAIResponsesClient(...).create_agent(...)` を利用し、`__init__.py` で `agent` をエクスポート。
- 可能なら簡易ワークフロー（例：分岐 or 直列）も同ディレクトリで対応可（`workflow` をエクスポート）。
- トラブルシュート: エンティティ未検出時は DevUI のギャラリー表示となるため、README でフォールバック挙動を明記。
