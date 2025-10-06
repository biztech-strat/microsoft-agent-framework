## workflows/parallel_gather_merge

概要
- 複数エージェントを並列実行し、集約（fan-out / fan-in）。

学べること
- ConcurrentBuilder の使い方
- カスタム集約（callback）

前提
- `az login` または API Key

実行
```bash
cd samples/workflows/parallel_gather_merge
python main.py            # 既定: 2並列
MAX_BRANCHES=3 python main.py
```

仕組み
- Dispatcher → participants（並列）→ Aggregator
