## workflows/sequential_pla-rtr-act

概要
- Plan → Retrieve → Act の直列ワークフロー（最小構成）。

学べること
- SequentialBuilder での直列接続
- Agent と Function Executor の混在

前提
- `az login` または API Key

実行
```bash
cd samples/workflows/sequential_pla-rtr-act
python main.py
```

仕組み
- Planner: 手順を3つに分解
- Retriever: 手順から疑似ノートを作成
- Actor: ノートから最終回答を生成
