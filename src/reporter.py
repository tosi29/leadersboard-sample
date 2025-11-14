"""Reporter - Generates HTML reports from benchmark results."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Template

DEFAULT_TEMPLATE_PATH = Path(__file__).with_name("templates") / "leaderboard.html"


def load_template(template_file: Optional[str] = None) -> Template:
    """Load the HTML template from disk."""
    template_path = Path(template_file) if template_file else DEFAULT_TEMPLATE_PATH

    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found at {template_path}")

    template_text = template_path.read_text(encoding="utf-8")
    return Template(template_text)


def _calculate_summary(tasks: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    summary = {"total": 0, "correct": 0, "incorrect": 0, "errors": 0}
    for task in tasks.values():
        summary["total"] += 1
        if task.get("error"):
            summary["errors"] += 1
        elif task.get("correct"):
            summary["correct"] += 1
        else:
            summary["incorrect"] += 1
    return summary


def _load_agent_files(results_dir: Path) -> Dict[str, Any]:
    agents: Dict[str, Dict[str, Any]] = {}
    latest_timestamp: Optional[str] = None

    for agent_file in sorted(results_dir.glob("*.json")):
        try:
            data = json.loads(agent_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        agent_name = data.get("agent_name") or agent_file.stem
        tasks_section = data.get("tasks", {})
        normalized_tasks: Dict[str, Dict[str, Any]] = {}

        for task_id, task_entry in tasks_section.items():
            task_result = task_entry.get("result")
            if not isinstance(task_result, dict):
                continue
            normalized_tasks[task_id] = task_result

        if not normalized_tasks:
            continue

        summary = data.get("summary")
        if not summary:
            summary = _calculate_summary(normalized_tasks)

        agents[agent_name] = {
            "tasks": normalized_tasks,
            "summary": summary,
        }

        timestamp = data.get("last_updated")
        if timestamp and (latest_timestamp is None or timestamp > latest_timestamp):
            latest_timestamp = timestamp

    return {
        "timestamp": latest_timestamp or "Unknown",
        "agents": agents,
    }


def _load_results(results_path: Path) -> Dict[str, Any]:
    if results_path.is_dir():
        return _load_agent_files(results_path)

    if results_path.is_file():
        try:
            with results_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass

    return {"timestamp": "Unknown", "agents": {}}


def generate_report(
    results_path: str = "results",
    output_file: str = "docs/index.html",
    template_file: Optional[str] = None,
) -> None:
    """
    Generate an HTML report from benchmark results.

    Args:
        results_path: Path to the results directory (or legacy JSON file)
        output_file: Path where the HTML report should be saved
        template_file: Optional override for the Jinja template path
    """
    path = Path(results_path)
    if not path.exists():
        print(f"Error: Results path not found at {results_path}")
        return

    results = _load_results(path)

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
        total_input_tokens = 0
        total_output_tokens = 0
        counted_input_tasks = 0
        counted_output_tasks = 0
        for task_id, task_info in agent_info.get("tasks", {}).items():
            execution_time = task_info.get("execution_time", 0)
            total_execution_time += execution_time
            input_tokens = task_info.get("input_tokens")
            output_tokens = task_info.get("output_tokens")

            if input_tokens is not None:
                total_input_tokens += input_tokens
                counted_input_tasks += 1
            if output_tokens is not None:
                total_output_tokens += output_tokens
                counted_output_tasks += 1

            tasks.append(
                {
                    "name": task_info.get("task_name", task_id),
                    "correct": task_info.get("correct", False),
                    "execution_time": execution_time,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                }
            )

        # Calculate average execution time
        average_time = (total_execution_time / total) if total > 0 else 0
        average_input_tokens = (
            total_input_tokens / counted_input_tasks if counted_input_tasks > 0 else 0
        )
        average_output_tokens = (
            total_output_tokens / counted_output_tasks if counted_output_tasks > 0 else 0
        )

        agents_data.append(
            {
                "name": agent_name,
                "accuracy": accuracy,
                "average_time": average_time,
                "average_input_tokens": average_input_tokens,
                "average_output_tokens": average_output_tokens,
                "correct": correct,
                "incorrect": incorrect,
                "total": total,
                "tasks": tasks,
            }
        )

    # Sort by accuracy (descending) and assign ranks
    agents_data.sort(key=lambda x: x["accuracy"], reverse=True)
    for i, agent in enumerate(agents_data, 1):
        agent["rank"] = i

    # Render template
    try:
        template = load_template(template_file)
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return

    html_content = template.render(
        timestamp=results.get("timestamp", "Unknown"),
        agents=agents_data,
    )

    # Save to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"HTML report generated at {output_file}")


def main():
    """Main entry point for the reporter"""
    import sys

    results_path = sys.argv[1] if len(sys.argv) > 1 else "results"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "docs/index.html"
    template_file = sys.argv[3] if len(sys.argv) > 3 else None

    generate_report(results_path, output_file, template_file)


if __name__ == "__main__":
    main()
