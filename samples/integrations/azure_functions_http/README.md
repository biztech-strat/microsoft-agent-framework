## integrations/azure_functions_http

概要
- Azure Functions（HTTP）の呼び出しをツール化。既定はモック、実HTTPにも切替可。

学べること
- ツールからの HTTP 呼び出しとエラー処理
- 関数キーの扱い（クエリ/ヘッダ）

前提（実HTTP時）
- `AZ_FUNCTION_URL` 必須、`AZ_FUNCTION_CODE` 任意

実行
```bash
cd samples/integrations/azure_functions_http
python main.py --name Taro          # mock
python main.py --name Taro --real 1 # real（環境変数を設定）
```

仕組み
- `call_function(name)` をツール化し、Agentが利用
- 例外は「Function call failed: ...」として整形
