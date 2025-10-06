# DevUI デモ（Microsoft Agent Framework）

DevUI を使って、ブラウザからエージェントを実行・デバッグする最小構成のデモです。ディレクトリ探索（CLI 起動）と、インメモリ登録（プログラム起動）の両方に対応します。

## 前提
- Python 3.10+
- このリポジトリ直下で実行（in-repo パッケージを優先利用）
- 認証のいずれか
  - `az login`（推奨）
  - もしくは、`.env` に `AZURE_OPENAI_API_KEY` を設定
- モデル設定
  - `.env` に少なくとも以下を設定
    - `AZURE_OPENAI_ENDPOINT`
    - `AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME`

> `.env` は DevUI が自動ロードします（エージェントディレクトリ、または `agents/` 親ディレクトリに配置）。サンプルは `samples/devui/agents/.env.sample` を用意しています。

## 1) ディレクトリ探索（CLI）で起動
> `devui` コマンドが見つからない場合は、`pip install agent-framework-devui --pre` を実行してください。
```
# 推奨: ルートで .env を準備するか、以下のどちらかへ設置
# - samples/devui/agents/.env
# - samples/devui/agents/weather_agent/.env

# DevUI 起動（エージェント自動検出）
devui ./samples/devui/agents --port 8080
# ブラウザ: http://localhost:8080
```
- エージェント一覧に「WeatherAgent」が表示され、チャット実行できます。
- トレーシングを有効化する場合
```
devui ./samples/devui/agents --port 8080 --tracing framework
```

## 2) プログラムで起動（インメモリ登録）
```
python samples/devui/main.py
# ブラウザが自動で開きます: http://localhost:8080
```

## フォルダ構成
```
samples/devui/
├── README.md
├── main.py                 # serve(entities=[agent]) で DevUI 起動
└── agents/
    ├── .env.sample         # 必要な環境変数のサンプル
    └── weather_agent/
        ├── __init__.py     # agent をエクスポート（DevUI 検出用）
        └── agent.py        # agent の実装（create_agent）
```

## 使っている主な API
- `agent_framework.azure.AzureOpenAIResponsesClient`
- `agent_framework.devui.serve`

## トラブルシュート
- エージェントが検出されない: `devui` の引数パスが `agents/` 直下を指しているか確認。
- モデル呼び出しで 401/403/404: `.env` の `AZURE_OPENAI_*` が正しいか確認（`az login` か API Key）。
- 画面上にサンプルギャラリーが表示される: エージェント未検出時のフォールバック動作です。`.env` 設定とディレクトリ構成を再確認してください。
