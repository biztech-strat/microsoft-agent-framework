 # MAF Samples (Custom)
 
 この `samples/` には、Microsoft Agent Framework（MAF）の機能をテーマ別に最小構成で示すサンプルを配置します。既存の `python/samples` に加えて、検証用の軽量サンプルと社内観点の追加説明を提供します。
 
 ## ローカル実行（リポジトリ直読み）
 MAFをpipインストールせずに、リポジトリのパッケージを直接参照して実行できます。
 
 ```bash
 # リポジトリ直下で一度だけ設定（シェルに合わせて調整）
 export PYTHONPATH="$PYTHONPATH:$(pwd)/python/packages/core:$(pwd)/python/packages/azure-ai"
 ```
 
 - 既に `agent_framework` と `agent_framework_azure_ai` が `PYTHONPATH` に入るため、
   `from agent_framework.azure import AzureOpenAIResponsesClient` などが利用できます。
 
 ## 認証と変数
 - Azure CLI 認証: `az login` を実行
 - もしくは `AZURE_OPENAI_API_KEY` を利用
 - 各サンプルの `.env.sample` を `.env` にコピーし、必要な値を設定してください。
 
 ## ディレクトリ
 - `samples/_shared/`: サンプル共通の環境読込・ロギング
 - `samples/basics/hello_agent/`: 最小のチャット（同期/ストリーム）
 
 ---
 
 詳細は各サンプルの `README.md` を参照してください。
