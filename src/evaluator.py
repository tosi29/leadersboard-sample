"""Evaluator - Evaluates agent outputs against expected answers"""

from typing import Dict, Any

def evaluate_result(agent_output: str, expected_answer: str, execution_success: bool) -> Dict[str, Any]:
    """
    Evaluate an agent's output against the expected answer

    Args:
        agent_output: The output produced by the agent
        expected_answer: The expected correct answer
        execution_success: Whether the agent executed successfully

    Returns:
        Dictionary with evaluation results including 'correct', 'reason'
    """
    # If execution failed, it's automatically incorrect
    if not execution_success:
        return {
            "correct": False,
            "reason": "Agent execution failed",
        }

    # If output is empty, it's incorrect
    if not agent_output or not agent_output.strip():
        return {
            "correct": False,
            "reason": "Agent produced no output",
        }

    # Check if the expected answer appears anywhere in the output
    if expected_answer.lower() in agent_output.lower():
        return {
            "correct": True,
            "reason": "Expected answer found in output",
        }

    return {
        "correct": False,
        "reason": f"Output does not match expected answer (expected: {expected_answer})",
    }


def calculate_accuracy(results: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate accuracy metrics from benchmark results

    Args:
        results: Dictionary of benchmark results

    Returns:
        Dictionary with accuracy metrics per agent
    """
    accuracies = {}

    for agent_name, agent_data in results.get("agents", {}).items():
        summary = agent_data.get("summary", {})
        total = summary.get("total", 0)

        if total > 0:
            correct = summary.get("correct", 0)
            accuracy = (correct / total) * 100
        else:
            accuracy = 0.0

        accuracies[agent_name] = {
            "accuracy": accuracy,
            "correct": summary.get("correct", 0),
            "total": total,
        }

    return accuracies

