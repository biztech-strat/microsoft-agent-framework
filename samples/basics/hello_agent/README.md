## basics/hello_agent

概要
- 最小のチャットエージェント。同期/ストリーミングの双方を確認できます。

学べること
- AzureOpenAIResponsesClient を用いたエージェント作成
- run / run_stream の使い分け

前提
- `az login` または `AZURE_OPENAI_API_KEY` を設定
- `.env.sample` を `.env` にコピー（必要ならエンドポイント/デプロイ名を編集）

実行
```bash
cd samples/basics/hello_agent
python main.py           # 同期→ストリーミングの順で出力
STREAM=1 python main.py  # ストリーミングのみ
```

オプション/入力
- 環境変数 `PROMPT` でユーザー入力を上書き

仕組み
- AzureOpenAIResponsesClient + AzureCliCredential（または API Key）で呼び出し
- ストリーミングはチャンクの `text` を逐次表示

ファイル
- `main.py`: 実行エントリ
- `.env.sample`: 必要な環境変数の雛形

トラブルシュート
- 認証エラー: `az login` または API Key 設定を確認
