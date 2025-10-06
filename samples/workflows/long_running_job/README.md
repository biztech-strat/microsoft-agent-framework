## workflows/long_running_job

概要
- 長時間ジョブ（外部処理）の起動→待機→再開（コールバック/ポーリング）。

学べること
- RequestInfoExecutor と checkpoint の使い方
- run_from_checkpoint / send_responses の再開パターン

実行
```bash
cd samples/workflows/long_running_job

# 1) ジョブ起動（IDとチェックポイントIDが出力されます）
python main.py start --text "レポートを生成"

# 2) 外部システムからの完了通知（コールバック）を模擬して再開
python main.py resume --checkpoint <CHECKPOINT_ID> --request <REQUEST_ID> --result "OK: 完了"

# オプション: 疑似ポーリング（3秒後に自動で再開）
python main.py demo_poll --text "ログ集計"
```

補足
- チェックポイントは `.checkpoints/` に保存
- RequestInfoEvent の `request_id` と checkpoint を控えてから再開
