# AI Agent Benchmark Leaderboard

AIエージェントのベンチマークとリーダーボードを構築・運用するためのシステムです。

## 特徴

- AIエージェントのベンチマーク実行
- 正誤判定
- 実行時間の計測
- HTMLレポート生成（GitHub Pages対応）

## プロジェクト構成

```
.
├── agents/                     # AIエージェントの定義（1ディレクトリ = 1エージェント）
│   ├── baseline/
│   │   └── agent.py
│   ├── gemini_2_5_flash/
│   │   └── agent.py
│   ├── with_code_executor/
│   │   └── agent.py
│   └── with_google_search/
│       └── agent.py
├── benchmarks/                 # ベンチマークタスクの定義
│   ├── task_001.json
│   ├── task_002.json
│   ├── task_003.json
│   ├── task_004.json
│   └── task_005.json
├── results/                    # 実行結果（JSONキャッシュ + 履歴）
├── src/                        # ソースコード
│   ├── __init__.py
│   ├── reporter.py             # HTMLレポート生成器
│   ├── runner.py               # ベンチマーク実行エンジン
│   └── services/
│       ├── __init__.py
│       ├── cache_manager.py    # テスト結果のキャッシュ
│       └── evaluator.py        # 評価ロジック
├── pyproject.toml              # uv設定
├── README.md
├── uv.lock
└── docs/ (generated)           # レポート生成後のHTML出力
```

## セットアップ

### 前提条件

- Python 3.11+
- uv（Pythonパッケージマネージャー）
- Google Cloud Project（Google ADK用）
- Google AI API Key

### インストール手順

1. リポジトリをクローン

```bash
git clone <repository-url>
cd leaderboard-sample
```

2. 依存関係をインストール

```bash
uv sync
```

3. （任意）開発用ツールのインストールとコミットフックの有効化

```bash
uv sync --group dev
pre-commit install
```

4. Google AI API Key を設定

```bash
export "GOOGLE_API_KEY=your_api_key_here"
```

または direnv を使う場合:

```bash
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

## 使い方

### 1. エージェントを作成

`agents/` ディレクトリに新しいエージェントファイルを作成します。

```python
from google.adk.agents.llm_agent import Agent

root_agent = Agent(
    model='gemini-2.5-flash',
    name='my_agent',
    description="エージェントの説明",
    instruction="エージェントの指示",
    tools=[],
)
```

### 2. ベンチマークタスクを作成

`benchmarks/` ディレクトリにタスク定義を追加します。

```json
{
  "name": "タスク名",
  "description": "タスクの説明",
  "query": "エージェントへのクエリ",
  "expected_answer": "期待する回答"
}
```

各タスクはファイル名（`.json`拡張子を除く）が自動的に識別子として使われます。カスタムIDが必要な場合を除き、`id` フィールドは省略できます。

### 3. ベンチマークを実行

```bash
uv run python src/runner.py
```

`--agent` を省略すると、利用可能なすべてのエージェントディレクトリを実行します。

特定のエージェントディレクトリのみを実行する場合は、`--agent` にディレクトリ名を渡します。

```bash
uv run python src/runner.py --agent baseline
```

各エージェントの最新結果は `results/<agent_name>.json` に保存されます。

#### コスト最適化のためのキャッシュ

ベンチマークランナーはファイルハッシュに基づいてテスト結果を自動的にキャッシュします。エージェントやベンチマークファイルが変更された場合のみ再実行されるため、トークンコストを大幅に削減できます。

**仕組み:**
- 各エージェントファイルのハッシュを計算し、テスト結果と一緒に保存
- 各ベンチマークタスクのハッシュも追跡
- 次回以降、ファイルが変わらなければキャッシュ結果を利用
- 変更されたエージェントのみを再テスト

**キャッシュ関連コマンド:**

```bash
# デフォルト実行（キャッシュがあれば利用）
uv run python src/runner.py

# キャッシュを無視して全テストを実行（キャッシュを更新）
uv run python src/runner.py --ignore-cache
```

**実行例:**
```
Found 4 agents and 5 benchmark tasks
Cache enabled: 15 cached results available

Running agent: gemini_2_5_flash
  Task: task_001 - 簡単な計算 [CACHED]
  Task: task_002 - やや複雑な計算
    Result: ✓ CORRECT (8.2s)

Cache Statistics:
  Cache hits: 3/5 (60.0%)
  New executions: 2/5 (40.0%)
```

キャッシュデータは `results/` 配下のエージェントごとの結果ファイルに保存されます。各JSONファイルにはエージェント／ベンチマークのハッシュが保存され、変更のない組み合わせは安全にスキップされます。

### 4. HTMLレポートを生成

```bash
uv run python src/reporter.py
```

デフォルトでは、すべての `results/*.json` を集計し、`docs/index.html` にHTMLを書き出します。

### 5. ローカルでレポートを閲覧

```bash
python -m http.server 8000 --directory docs
```

> **Note:** `docs/` ディレクトリは `uv run python src/reporter.py` 実行時に生成されます。存在しない場合は先にレポートを生成してください。

ブラウザで `http://localhost:8000` を開きます。

## GitHub Pages へのデプロイ

1. リポジトリの Settings > Pages を開く
2. Source を「Deploy from a branch」に設定
3. Branch を `main`（または任意のブランチ）、フォルダを `/docs` に設定
4. `https://<username>.github.io/<repository>/` で公開されます

## GitHub Actions 連携

自動ベンチマークは `.github/workflows/bench-report.yml` で提供されます。
このワークフローは `main` ブランチへのプッシュ時、または手動で実行できます。ベンチマーク実行で Google AI API にアクセスできるよう、`GOOGLE_API_KEY` シークレットを設定してください。ワークフローの手順は次のとおりです。

1. リポジトリをチェックアウト
2. `uv` で依存関係をインストール
3. ベンチマークスイートを実行（`src/runner.py`）
4. HTMLレポートを生成（`src/reporter.py`）
5. `docs/` の内容を `peaceiris/actions-gh-pages` を使って GitHub Pages に公開

トリガー条件の変更やデプロイ方法のカスタマイズが必要な場合は、ワークフローを編集してください。

## 評価指標

現在サポートしている指標:

- 正誤判定（期待する回答に対する大文字小文字を区別しない部分一致）
- 実行時間
- トークン数（入出力の平均をレポートに表示）

## カスタマイズ

### 評価ロジックの変更

`src/services/evaluator.py` の `evaluate_result()` を編集してください。

### HTMLテンプレートの変更

`src/templates/leaderboard.html` を編集してください。

