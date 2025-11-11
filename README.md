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
│   ├── task1.json
│   ├── task2.json
│   ├── task3.json
│   ├── task4.json
│   └── task5.json
├── results/                    # Execution results (JSON cache + history)
├── src/                        # Source code
│   ├── __init__.py
│   ├── cache_manager.py        # Test result caching
│   ├── evaluator.py            # Evaluation logic
│   ├── reporter.py             # HTML report generator
│   └── runner.py               # Benchmark execution engine
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
  "id": "task_003",
  "name": "Task name",
  "description": "Task description",
  "query": "Query for the agent",
  "expected_answer": "Expected answer"
}
```

### 3. Run benchmarks

```bash
uv run python src/runner.py
```

Results are saved to `results/benchmark_results.json`.

#### Caching for Cost Optimization

The benchmark runner automatically caches test results based on file hashes. This significantly reduces token costs by only re-running tests when agent or benchmark files change.

**How it works:**
- Each agent file's hash is computed and stored with test results
- Each benchmark task's hash is also tracked
- On subsequent runs, cached results are used if files haven't changed
- Only modified agents are re-tested

**Cache commands:**

```bash
# Run with cache (default)
uv run python src/runner.py

# Run without cache (force all tests)
uv run python src/runner.py --no-cache

# Clear cache before running
uv run python src/runner.py --clear-cache
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

The cache file is stored at `results/benchmark_cache.json`.

### 4. Generate HTML report

```bash
uv run python src/reporter.py
```

The report is generated at `docs/index.html`.

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
- Token count (placeholder, to be implemented)

## Customization

### Custom evaluation logic

Edit `evaluate_result()` in `src/evaluator.py`.

### Custom HTML template

Edit `HTML_TEMPLATE` in `src/reporter.py`.

## Troubleshooting

### Google ADK not found

```bash
uv add google-adk
```

### API Key error

Check that `.env` file contains valid Google AI API Key.

## License

MIT License
