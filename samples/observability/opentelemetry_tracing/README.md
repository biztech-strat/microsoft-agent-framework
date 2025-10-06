## observability/opentelemetry_tracing

概要
- OpenTelemetry で最小のトレーシング（ConsoleSpanExporter）。

学べること
- ワークフロー/エグゼキュータのスパン構成
- カスタム属性・イベントの付与

実行
```bash
cd samples/observability/opentelemetry_tracing
python main.py
```

出力
- コンソールにスパン（名前・属性・親子関係）が表示
