## identity/managed_identity

概要
- Managed Identity（クラウド）/ DefaultAzureCredential（ローカル）で Graph `/me`。

実行
```bash
cd samples/identity/managed_identity
python main.py --mock 1
python main.py            # az login 後
```

仕組み
- DefaultAzureCredential→トークン取得→httpx で `/me`
