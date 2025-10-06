## integrations/rest_basic

概要
- REST API 呼び出しの最小例（成功/失敗/429）をツール化。既定はモックでネットワーク不要。

学べること
- ツールでのエラー/レート制限の人間可読ハンドリング
- 実APIへの切替（httpx）

実行
```bash
cd samples/integrations/rest_basic
python main.py --city 東京                 # success
python main.py --city 東京 --mode fail     # failure
python main.py --city 東京 --mode rate_limit  # 429
```

オプション
- `--real --url <endpoint>` で実APIに切替（`httpx` が必要）

仕組み
- `RestClient` の `mode` により応答/例外を模擬
- `fetch_weather(city)` をツールとして公開し、エージェントが利用
