# AI Agent Benchmark Leaderboard

AI agent benchmark and leaderboard system.

## Features

- Benchmark execution for AI agents
- Correct/Incorrect evaluation
- Execution time measurement
- HTML report generation (GitHub Pages ready)
- Extensible evaluation framework

## Project Structure

```
.
├── agents/              # AI agent definitions (1 file = 1 agent)
│   ├── agent_v1.py
│   └── agent_baseline.py
├── benchmarks/          # Benchmark task definitions
│   ├── task1.json
│   └── task2.json
├── src/                 # Source code
│   ├── runner.py       # Benchmark execution engine
│   ├── evaluator.py    # Evaluation logic
│   └── reporter.py     # HTML report generator
├── test_files/          # Test files
│   └── scenario1/
├── results/             # Execution results (JSON)
├── docs/                # HTML reports (for GitHub Pages)
└── pyproject.toml       # uv configuration
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

3. Set Google AI API Key

```bash
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

## Usage

### 1. Create an agent

Create a new agent file in the `agents/` directory.

```python
# agents/my_agent.py
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
  "expected_answer": "Expected answer",
  "test_directory": "test_files/scenario1"
}
```

### 3. Run benchmarks

```bash
uv run python src/runner.py
```

Results are saved to `results/benchmark_results.json`.

### 4. Generate HTML report

```bash
uv run python src/reporter.py
```

The report is generated at `docs/index.html`.

### 5. View report locally

```bash
python -m http.server 8000 --directory docs
```

Open `http://localhost:8000` in your browser.

## GitHub Pages Deployment

1. Go to repository Settings > Pages
2. Set Source to "Deploy from a branch"
3. Set Branch to `main` (or your branch) and folder to `/docs`
4. The report will be published at `https://<username>.github.io/<repository>/`

## GitHub Actions Integration (Future)

Create `.github/workflows/benchmark.yml` for automated benchmarking:

```yaml
name: Run Benchmarks

on:
  schedule:
    - cron: '0 0 * * 0'  # Run weekly
  workflow_dispatch:

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: uv sync
      - name: Run benchmarks
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: uv run python src/runner.py
      - name: Generate report
        run: uv run python src/reporter.py
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
```

## Evaluation Metrics

Currently supported:

- Correct/Incorrect (file path matching)
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
