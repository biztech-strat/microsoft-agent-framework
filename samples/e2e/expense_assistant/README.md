## e2e/expense_assistant

企業内の経費精算アシストを想定したエンドツーエンド（E2E）サンプルです。

構成（WorkflowBuilder）
- Parser: 入力テキストから明細を抽出（カテゴリー/金額/日付）
- PolicyCheck: 社内ポリシー（例: 食事は1,500円以内、合計上限 20,000円）
- Switch: OK→Submit, NG→Explain
- Submit: Graph からユーザー名を取得（モック/実）してレポート登録（モック）
- Explain: 違反理由をエージェントで日本語説明

### 前提
- Python 3.10+
- 本リポジトリ直読みのためのブートストラップは各 `main.py` が自動実行します（追加設定不要）
- Graphの実呼び出しを行う場合のみ、Azure CLI で `az login` 済みであること

### 入力フォーマット
- テキスト1行に、経費明細をカンマ区切りで並べます
- 各明細は「カテゴリ語 +（任意の日付 YYYY-MM-DD）+ 金額（〜円）」の順で含めてください
- カテゴリの判定（簡易）
  - 「タクシー」を含む → taxi
  - 「昼食」「ランチ」を含む → meal
  - それ以外 → その他

例: `タクシー 2025-09-15 3200円, 昼食 1200円`

### 実行（シンプルルート: 即時確定）
```bash
cd samples/e2e/expense_assistant

# 例: 2件の経費（タクシー3,200円・昼食1,200円）
python main.py --text "タクシー 2025-09-15 3200円, 昼食 1200円"

# ポリシー違反の例（昼食2,300円）
python main.py --text "昼食 2300円"

# Graphの実呼び出し（任意）
# 事前に az login 済み、必要なら GRAPH_BASE/GRAPH_SCOPE を設定
python main.py --text "タクシー 1800円" --graph-real 1

# （発展）承認フローつき: 高額時は承認待ちで停止→再開（多段承認 + RAG根拠提示）
python approval_flow.py start --text "タクシー 12000円, 昼食 1200円"
# 出力された request_id / checkpoint_id を用いて承認
python approval_flow.py approve --checkpoint <CHECKPOINT_ID> --request <REQUEST_ID> --approved 1 --comment ok
```

### 承認フローの挙動（多段化）
- 合計 > 10,000 円 かつ OK 判定の申請は「上長承認」へ
- 合計 > 15,000 円 なら、上長承認後に「経理承認」へ自動的に再申請
- checkpoint は `samples/e2e/expense_assistant/.checkpoints/` に保存されます
- start 実行時の出力例
  - `[request] id=<REQ> total_yen=<合計>` … 承認に必要な `request_id`
  - `[checkpoint] id=<CP>` … 再開に必要な `checkpoint_id`
- 承認再開コマンド例
  - `python approval_flow.py approve --checkpoint <CP> --request <REQ> --approved 1 --comment ok`

### RAG（根拠付き説明）
- 違反時は `policy.md` から該当セクションを抽出して「根拠」を提示します
- Explain出力に「根拠:」節が付与され、ポリシーの抜粋（例: 食事上限/上長・経理承認の閾値等）が表示されます

環境変数（任意）
- `GRAPH_SCOPE` 既定: `https://graph.microsoft.com/.default`
- `GRAPH_BASE` 既定: `https://graph.microsoft.com/v1.0`

### トラブルシュート
- `ModuleNotFoundError: agent_framework` が出る
  - 本サンプルは `samples/_shared/bootstrap.py` により自動でリポ内パスを解決します。エラーが続く場合は、リポ直下で `export PYTHONPATH="$PYTHONPATH:$(pwd)/python/packages/core:$(pwd)/python/packages/azure-ai"` を試してください。
- `httpx` が見つからない / Graph 実呼び出しでエラー
  - `pip install httpx` を実施し、`az login` 済みか確認してください。
- 承認フローで `checkpoint_id/request_id` を控え忘れた
  - `.checkpoints` ディレクトリの最新ファイルの中身から `checkpoint_id` を取得できます。`request_id` は `start` 実行のログにのみ出るため、再度 `start` をやり直してください。
