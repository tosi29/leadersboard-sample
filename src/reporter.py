"""Reporter - Generates HTML reports from benchmark results"""

import json
from pathlib import Path

from jinja2 import Template

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Agent Benchmark Leaderboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont,
                'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell,
                sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }

        .header p {
            opacity: 0.9;
            font-size: 1.1rem;
        }

        .content {
            padding: 2rem;
        }

        .timestamp {
            text-align: center;
            color: #666;
            margin-bottom: 2rem;
            font-size: 0.9rem;
        }

        .leaderboard {
            margin-bottom: 3rem;
        }

        .leaderboard h2 {
            color: #333;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #667eea;
        }

        .agent-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border-left: 4px solid #667eea;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .agent-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .agent-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }

        .agent-name {
            font-size: 1.4rem;
            font-weight: 600;
            color: #333;
        }

        .rank-badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9rem;
        }

        .rank-badge.rank-1 {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }

        .rank-badge.rank-2 {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }

        .rank-badge.rank-3 {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }

        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }

        .metric {
            background: white;
            padding: 1rem;
            border-radius: 6px;
            text-align: center;
        }

        .metric-label {
            font-size: 0.85rem;
            color: #666;
            margin-bottom: 0.25rem;
        }

        .metric-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #333;
        }

        .metric-value.accuracy {
            color: #667eea;
        }

        .metric-value.correct {
            color: #43e97b;
        }

        .metric-value.incorrect {
            color: #f5576c;
        }

        .task-details {
            margin-top: 2rem;
        }

        .task-details h3 {
            color: #333;
            margin-bottom: 1rem;
            font-size: 1.1rem;
        }

        .task-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 6px;
            overflow: hidden;
        }

        .task-table th {
            background: #667eea;
            color: white;
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
        }

        .task-table td {
            padding: 0.75rem;
            border-bottom: 1px solid #eee;
        }

        .task-table tr:last-child td {
            border-bottom: none;
        }

        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
            display: inline-block;
        }

        .status-correct {
            background: #d4f4dd;
            color: #1e7e34;
        }

        .status-incorrect {
            background: #f8d7da;
            color: #721c24;
        }

        .footer {
            text-align: center;
            padding: 2rem;
            color: #666;
            border-top: 1px solid #eee;
            font-size: 0.9rem;
        }

        .no-data {
            text-align: center;
            padding: 3rem;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI Agent Benchmark Leaderboard</h1>
            <p>Performance evaluation and comparison</p>
        </div>

        <div class="content">
            <div class="timestamp">
                Last updated: {{ timestamp }}
            </div>

            <div class="leaderboard">
                <h2>Leaderboard Rankings</h2>

                {% if agents %}
                    {% for agent in agents %}
                    <div class="agent-card">
                        <div class="agent-header">
                            <div class="agent-name">{{ agent.name }}</div>
                            <div class="rank-badge rank-{{ agent.rank }}">
                                Rank #{{ agent.rank }}
                            </div>
                        </div>

                        <div class="metrics">
                            <div class="metric">
                                <div class="metric-label">Accuracy</div>
                                <div class="metric-value accuracy">
                                    {{ "%.1f"|format(agent.accuracy) }}%
                                </div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">Average Time</div>
                                <div class="metric-value">
                                    {{ "%.2f"|format(agent.average_time) }}s
                                </div>
                            </div>
                        </div>

                        <div class="task-details">
                            <h3>Task Results</h3>
                            <table class="task-table">
                                <thead>
                                    <tr>
                                        <th>Task</th>
                                        <th>Status</th>
                                        <th>Time (s)</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for task in agent.tasks %}
                                    <tr>
                                        <td>{{ task.name }}</td>
                                        <td>
                                            <span class="status-badge status-{{
                                                'correct' if task.correct else 'incorrect'
                                            }}">
                                                {{ 'CORRECT' if task.correct else 'INCORRECT' }}
                                            </span>
                                        </td>
                                        <td>{{ "%.2f"|format(task.execution_time) }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="no-data">
                        No benchmark results available yet. Run the benchmarks to generate data.
                    </div>
                {% endif %}
            </div>
        </div>

        <div class="footer">
            Generated by AI Agent Benchmark System
        </div>
    </div>
</body>
</html>
"""


def generate_report(results_file: str = "results/benchmark_results.json",
                   output_file: str = "docs/index.html") -> None:
    """
    Generate an HTML report from benchmark results

    Args:
        results_file: Path to the JSON results file
        output_file: Path where the HTML report should be saved
    """
    # Load results
    results_path = Path(results_file)
    if not results_path.exists():
        print(f"Error: Results file not found at {results_file}")
        return

    with open(results_path, 'r') as f:
        results = json.load(f)

    # Prepare data for template
    agents_data = []

    for agent_name, agent_info in results.get("agents", {}).items():
        summary = agent_info.get("summary", {})
        total = summary.get("total", 0)
        correct = summary.get("correct", 0)
        incorrect = summary.get("incorrect", 0)

        accuracy = (correct / total * 100) if total > 0 else 0

        # Collect task details
        tasks = []
        total_execution_time = 0
        for task_id, task_info in agent_info.get("tasks", {}).items():
            execution_time = task_info.get("execution_time", 0)
            total_execution_time += execution_time
            tasks.append({
                "name": task_info.get("task_name", task_id),
                "correct": task_info.get("correct", False),
                "execution_time": execution_time,
            })

        # Calculate average execution time
        average_time = (total_execution_time / total) if total > 0 else 0

        agents_data.append({
            "name": agent_name,
            "accuracy": accuracy,
            "average_time": average_time,
            "correct": correct,
            "incorrect": incorrect,
            "total": total,
            "tasks": tasks,
        })

    # Sort by accuracy (descending) and assign ranks
    agents_data.sort(key=lambda x: x["accuracy"], reverse=True)
    for i, agent in enumerate(agents_data, 1):
        agent["rank"] = i

    # Render template
    template = Template(HTML_TEMPLATE)
    html_content = template.render(
        timestamp=results.get("timestamp", "Unknown"),
        agents=agents_data,
    )

    # Save to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(html_content)

    print(f"HTML report generated at {output_file}")


def main():
    """Main entry point for the reporter"""
    import sys

    results_file = sys.argv[1] if len(sys.argv) > 1 else "results/benchmark_results.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "docs/index.html"

    generate_report(results_file, output_file)


if __name__ == "__main__":
    main()
