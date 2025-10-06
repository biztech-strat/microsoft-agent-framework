## basics/tool_calling_single

概要
- 関数ツールを1つ公開し、エージェントが自動選択で呼び出す最小例。

学べること
- ツールの型定義（Annotated + Field）
- ツール呼び出しのログと返却フォーマット

前提
- `az login` または API Key
- `.env.sample` → `.env`

実行
```bash
cd samples/basics/tool_calling_single
python main.py
```

オプション/入力
- 実行時のユーザー入力はコード内で固定（「今日の東京の天気は？」）

仕組み
- `get_weather(location: str) -> str` をツールとして公開
- エージェントが必要に応じてツールを呼び出し、結果を応答に組み込み

ファイル
- `main.py`: ツール定義とエージェント実行
- `.env.sample`

トラブルシュート
- ツールが呼ばれない: プロンプトがツール利用を誘発する内容か確認
