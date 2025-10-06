## basics/memory_short_term

概要
- 同一スレッドを共有して短期メモリ（履歴参照）を実現する例。

学べること
- `AgentThread` の生成/再利用
- run と run_stream の混在

前提
- `az login` または API Key

実行
```bash
cd samples/basics/memory_short_term
python main.py
```

期待される動作
- 1ターン目: 「私の好きな色は青」→ 応答
- 2ターン目: 「私の好きな色は？」→ 「青」と参照して応答

仕組み
- `thread = agent.get_new_thread()` を作成して両ターンで渡す

トラブルシュート
- 記憶されない: 同じ `thread` を run/run_stream に渡しているか確認
