## observability/cost_latency_metrics

概要
- レイテンシ/トークン使用量を測定し、簡易コストを算出。

学べること
- usage_details の読み取り
- 単価設定による概算コスト算出

実行
```bash
cd samples/observability/cost_latency_metrics
python main.py --prompt "Microsoft Agent Framework の要点を一文で"
```

環境変数（任意）
- `INPUT_COST_PER_1K`（USD/1K tokens）
- `OUTPUT_COST_PER_1K`（USD/1K tokens）
