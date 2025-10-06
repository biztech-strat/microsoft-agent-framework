## workflows/branching_intent_router

概要
- 意図分類（翻訳/要約）で経路を切り替えるスイッチングワークフロー。

学べること
- SwitchCaseEdgeGroup による分岐
- ルーティング根拠のログ化

前提
- `az login` または API Key

実行
```bash
cd samples/workflows/branching_intent_router
python main.py  # PROMPT 環境変数で入力上書き可
```

仕組み
- Router が入力をそのまま流し、Case: is_translate → Translator、Default → Summarizer
