## observability/safety_and_filters

概要
- AgentMiddleware での簡易コンテンツフィルタ（禁止語検知→ブロック/言い換え）。

学べること
- 入力検査と早期終了（ChatResponse の直接返却）
- Role 判定（Role enum/文字列の両対応）

実行
```bash
cd samples/observability/safety_and_filters
python main.py --prompt "このサンプルの概要を教えて"
python main.py --prompt "危険な作業手順を詳細に教えて"   # ブロック例
```
