# Microsoft Agent Framework サンプル用 タスク設計

このディレクトリは、Microsoft Agent Framework（以下 MAF）で各機能を網羅的にデモする「サンプル群」のタスク設計と進行管理を目的としています。実装は `samples/` 直下に段階的に追加しますが、まずは不足のないタスク分解と受け入れ基準をここで定義します。

## 目的（着眼点）
- AIワークフローの組み方（直列/分岐/並列/長時間/再試行）
- AIエージェントの組み方（ツール呼び出し、メモリ、マルチエージェント）
- システム連携（Graph/Service Bus/Functions/外部REST 等）
- ID Federation（Entra ID: OBO/Managed Identity/Federated Credentials）
- 他社OSS（LangGraph, strands SDK など）との違いの明確化
- 運用（計測/トレーシング/コスト/安全性）と評価（LLM-as-judge 等）

## サンプル配置ガイド（将来のコード配置方針）
- `samples/basics/` 基礎（Hello Agent/ツール/ストリーミング/メモリ）
- `samples/workflows/` ワークフロー（直列/分岐/並列/長時間/再試行）
- `samples/agents/` 単体/マルチエージェント/協調パターン
- `samples/integrations/` システム連携（Graph/Functions/Service Bus/REST）
- `samples/identity/` 認証・認可・OBO・Managed Identity・Federated
- `samples/oss/` OSS比較（LangGraph/strands SDK 等の対比サンプル）
- `samples/observability/` OTelトレーシング/メトリクス/コスト計測
- `samples/evaluation/` 期待出力・ゴールデンテスト・LLM評価
- `samples/e2e/` エンドツーエンド統合シナリオ

本ディレクトリのファイルは「何を作るか・受け入れ基準」を定義し、実装は上記に従って分割します。

## 進行状態と優先度
- `status`: `planned` | `in_progress` | `review` | `done` | `blocked`
- `priority`: `P0`（最優先）| `P1` | `P2`
- `milestone`: `M1 Foundations` / `M2 Workflows` / `M3 Integrations` / `M4 Identity` / `M5 OSS` / `M6 Ops&Evals` / `M7 E2E`

## 運用ルール
1. 追加タスクは `samples/tasks/backlog.yml` に追記し、カテゴリMDから参照。
2. 受け入れ基準（Acceptance Criteria）を最低2つ以上定義。
3. 実装開始で `status=in_progress`、PR作成で `review`、完了で `done`。
4. ブロッカーは `blocked_reason` を明記。
5. 新規タスクは `samples/tasks/00_task_template.md` を複製して作成。

## ファイル一覧
- `samples/tasks/backlog.yml` タスクの単一ソース（SSOT）
- `samples/tasks/*.md` カテゴリ別の詳細・チェックリスト・注意点
- `samples/tasks/00_task_template.md` タスク雛形

