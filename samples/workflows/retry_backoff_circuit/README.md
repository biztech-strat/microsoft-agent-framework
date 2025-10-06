## workflows/retry_backoff_circuit

不安定な処理に対して、リトライ・指数バックオフ・サーキットブレーカを適用する最小例です。

### 実行
```bash
cd samples/workflows/retry_backoff_circuit
python main.py --text "レポート生成" --fail-first 2 --max-retries 5 --base-delay 0.3 --timeout 1.0 \
  --circuit-threshold 3 --circuit-reset-sec 5
```

### オプション
- `--fail-first N`: 最初のN回は強制失敗（失敗注入）
- `--max-retries`: リトライ回数
- `--base-delay`: バックオフの基底秒（指数 2^attempt-1）
- `--timeout`: 単回試行タイムアウト（秒）
- `--circuit-threshold`: 連続失敗でサーキットを開く閾値
- `--circuit-reset-sec`: オープン後のクールダウン秒

### 期待されるログ出力
- 各試行の成否/遅延/エラー内容
- サーキット開閉（open/half-open/closed）の遷移

