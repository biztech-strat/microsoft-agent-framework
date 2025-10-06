## identity/federated_credentials_gha

概要
- GitHub Actions OIDC を用いたシークレットレスな Azure ログインの最小構成。

手順の概要
1) Entra ID でアプリ登録（client-id取得）
2) アプリ登録 > Federated credentials でリポジトリ/ブランチを紐づけ
3) リポジトリに以下のワークフローを配置
4) `azure/login` で OIDC ログイン→ az コマンド実行

最小ワークフロー例（.github/workflows/oidc-deploy.yml）
```yaml
name: OIDC Deploy
on:
  workflow_dispatch:

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      - name: Show whoami
        run: |
          az account show
```

注記
- `AZURE_CLIENT_ID` は Federated Credentials を構成したアプリの Application (client) ID。リポジトリ Secrets に保存。
