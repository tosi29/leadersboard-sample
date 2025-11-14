# AI Agent Benchmark Leaderboard

AI agent benchmark and leaderboard system.

## Features

- Benchmark execution for AI agents
- Correct/Incorrect evaluation
- Execution time measurement
- HTML report generation (GitHub Pages ready)

## Project Structure

```
.
├── agents/                     # AI agent definitions (1 directory = 1 agent)
│   ├── baseline/
│   │   └── agent.py
│   ├── gemini_2_5_flash/
│   │   └── agent.py
│   ├── with_code_executor/
│   │   └── agent.py
│   └── with_google_search/
│       └── agent.py
├── benchmarks/                 # Benchmark task definitions
│   ├── task_001.json
│   ├── task_002.json
│   ├── task_003.json
│   ├── task_004.json
│   └── task_005.json
├── results/                    # Execution results (JSON cache + history)
├── src/                        # Source code
│   ├── __init__.py
│   ├── reporter.py             # HTML report generator
│   ├── runner.py               # Benchmark execution engine
│   └── services/
│       ├── __init__.py
│       ├── cache_manager.py    # Test result caching
│       └── evaluator.py        # Evaluation logic
├── pyproject.toml              # uv configuration
├── README.md
├── uv.lock
└── docs/ (generated)           # HTML reports after running reporter
```

## Setup

### Prerequisites

- Python 3.11+
- uv (Python package manager)
- Google Cloud Project (for Google ADK)
- Google AI API Key

### Installation

1. Clone the repository

```bash
git clone <repository-url>
cd leadersboard-sample
```

2. Install dependencies

```bash
uv sync
```

3. (Optional) Install development tooling and enable commit hooks

```bash
uv sync --group dev
pre-commit install
```

4. Set Google AI API Key
```bash
export "GOOGLE_API_KEY=your_api_key_here"
```


or Use direnv.
```bash
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

## Usage

### 1. Create an agent

Create a new agent file in the `agents/` directory.

```python
from google.adk.agents.llm_agent import Agent

root_agent = Agent(
    model='gemini-2.5-flash',
    name='my_agent',
    description="Agent description",
    instruction="Agent instructions",
    tools=[],
)
```

### 2. Create benchmark tasks

Create task definitions in the `benchmarks/` directory.

```json
{
  "name": "Task name",
  "description": "Task description",
  "query": "Query for the agent",
  "expected_answer": "Expected answer"
}
```

Each task automatically uses its filename (without the `.json` extension) as the identifier, so you can omit the `id` field unless you need a custom value.

### 3. Run benchmarks

```bash
uv run python src/runner.py
```

If you omit `--agent`, the runner executes every available agent directory.

To run benchmarks for a single agent directory, pass its name with `--agent`:

```bash
uv run python src/runner.py --agent baseline
```

Each agent's latest results are saved to `results/<agent_name>.json`.

#### Caching for Cost Optimization

The benchmark runner automatically caches test results based on file hashes. This significantly reduces token costs by only re-running tests when agent or benchmark files change.

**How it works:**
- Each agent file's hash is computed and stored with test results
- Each benchmark task's hash is also tracked
- On subsequent runs, cached results are used if files haven't changed
- Only modified agents are re-tested

**Cache commands:**

```bash
# Default run (uses cached results when available)
uv run python src/runner.py

# Ignore cached results (force all tests while updating the cache)
uv run python src/runner.py --ignore-cache
```

**Example output:**
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

Cached data now lives in the per-agent result files under `results/`. Each JSON file
stores the agent/benchmark hashes for every task so unchanged combinations are safely
skipped.

### 4. Generate HTML report

```bash
uv run python src/reporter.py
```

By default the reporter aggregates every `results/*.json` file and writes the HTML to
`docs/index.html`.

### 5. View report locally

```bash
python -m http.server 8000 --directory docs
```

> **Note:** The `docs/` directory is created when you run `uv run python src/reporter.py`. If it does not exist yet, generate the report first.

Open `http://localhost:8000` in your browser.

## GitHub Pages Deployment

1. Go to repository Settings > Pages
2. Set Source to "Deploy from a branch"
3. Set Branch to `main` (or your branch) and folder to `/docs`
4. The report will be published at `https://<username>.github.io/<repository>/`

## GitHub Actions Integration

Automated benchmarking is provided via `.github/workflows/bench-report.yml`.
The workflow runs on pushes to the `main` branch and can also be triggered
manually. Make sure to configure the `GOOGLE_API_KEY` secret so the benchmark
run can access the Google AI APIs. The workflow performs the following steps:

1. Checks out the repository
2. Installs dependencies with `uv`
3. Runs the benchmark suite (`src/runner.py`)
4. Generates the HTML report (`src/reporter.py`)
5. Publishes the contents of `docs/` to GitHub Pages using
   `peaceiris/actions-gh-pages`

Update the workflow if you need to change the trigger conditions or customize
the deployment behaviour.

## Evaluation Metrics

Currently supported:

- Correct/Incorrect (case-insensitive substring matching against the expected answer)
- Execution time
- Token count (input/output averages shown in the report)

## Customization

### Custom evaluation logic

Edit `evaluate_result()` in `src/services/evaluator.py`.

### Custom HTML template

Edit `src/templates/leaderboard.html`.

## Troubleshooting

### Google ADK not found

```bash
uv add google-adk
```

### API Key error

Check that `.env` file contains valid Google AI API Key.

## License

MIT License
