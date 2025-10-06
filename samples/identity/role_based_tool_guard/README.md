## identity/role_based_tool_guard

概要
- ロールに応じてツール呼び出しを許可/拒否するガードの最小例。

学べること
- デコレータでのロールチェック
- 例外（PermissionError）の取り扱い

実行
```bash
cd samples/identity/role_based_tool_guard
python main.py --roles admin  --query "売上データを集計して"
python main.py --roles reader --query "売上データを集計して"  # 拒否例
```
