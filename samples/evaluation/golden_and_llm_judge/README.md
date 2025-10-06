## evaluation/golden_and_llm_judge

概要
- ゴールデンテストと LLM 採点（LLM-as-judge）の最小ハーネス。

学べること
- 正規化比較の実装
- 採点プロンプトとしきい値判定

実行
```bash
cd samples/evaluation/golden_and_llm_judge
python main.py run --case basics
python main.py judge --case basics --threshold 0.8
```

仕組み
- `golden.json` に期待条件（contains）を記述
- `run`: normalize後に部分一致で合否判定
- `judge`: 別Agentが 0..1 のスコアを返し、しきい値で判定
