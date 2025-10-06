## basics/structured_output

概要
- Pydantic モデルで構造化出力を受け取り、検証失敗時に再試行します。

学べること
- `response_format=Model` の利用
- 検証エラー時のリトライ制御

前提
- `az login` または API Key

実行
```bash
cd samples/basics/structured_output
python main.py
```

オプション/入力
- コード内のプロンプトを編集してテーマ変更可能

仕組み
- `Summary` モデル（topic, bullets[3]）に沿って応答を JSON として検証
- 失敗時はプロンプトに「JSONのみ」等の強化指示を付与して再送

トラブルシュート
- 型不一致: bulletsが3件か、必須キーが埋まっているか確認
