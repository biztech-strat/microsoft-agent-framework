## integrations/msgraph_me_profile

概要
- Microsoft Graph `/me` の取得（モック/実リクエスト両対応）。

学べること
- Azure CLI 認証での Graph 呼び出し
- モックでのオフライン動作

実行
```bash
cd samples/integrations/msgraph_me_profile
python main.py --mock 1   # モック
python main.py            # 実リクエスト（az login 済み）
```

環境変数（任意）
- `GRAPH_SCOPE`（既定: `https://graph.microsoft.com/.default`）
- `GRAPH_BASE`（既定: `https://graph.microsoft.com/v1.0`）
