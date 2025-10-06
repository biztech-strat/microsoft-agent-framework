## integrations/azure_service_bus

概要
- Service Bus との非同期連携（モック/実接続）。並列処理とデッドレターを再現。

学べること
- 送信/受信ワーカーと再試行・デッドレター
- 実接続への切替

環境変数（実接続）
- `AZ_SERVICEBUS_CONNECTION`, `AZ_SERVICEBUS_QUEUE`

実行
```bash
cd samples/integrations/azure_service_bus
python main.py demo --count 10 --concurrency 2 --fail-ratio 0.2
python main.py send --text "hello" --real 1
python main.py worker --real 1 --concurrency 4
```

仕組み
- デモは `asyncio.Queue` を利用
- 実接続は `azure-servicebus` を利用
