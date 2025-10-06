## identity/obo_web_to_graph

概要
- OBO（On-behalf-of）で user assertion → Graph トークン交換 → `/me`。CLIで流れを模擬。

前提
- モック時は不要。実行時は `AZURE_TENANT_ID/CLIENT_ID/CLIENT_SECRET` を設定し、`--user-assertion` を指定。

実行
```bash
cd samples/identity/obo_web_to_graph
python main.py --mock 1
python main.py --user-assertion <JWT>
```

仕組み
- `OnBehalfOfCredential` で下流 Graph 用トークンを取得後、`/me` を呼び出し
