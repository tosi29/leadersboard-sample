"""Evaluator - Evaluates agent outputs against expected answers"""

import re
from typing import Dict, Any
from pathlib import Path


def normalize_path(path_str: str) -> str:
    """
    Normalize a file path for comparison
    - Remove leading/trailing whitespace
    - Convert to Path and back to get normalized format
    - Handle both absolute and relative paths
    """
    if not path_str:
        return ""

    path_str = path_str.strip()

    # Try to extract path from common formats like "FOUND: path/to/file"
    patterns = [
        r'FOUND:\s*(.+)',
        r'PATH:\s*(.+)',
        r'File:\s*(.+)',
        r'Location:\s*(.+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, path_str, re.IGNORECASE)
        if match:
            path_str = match.group(1).strip()
            break

    # Normalize the path
    try:
        normalized = str(Path(path_str).as_posix())
        return normalized
    except:
        return path_str


def paths_match(path1: str, path2: str) -> bool:
    """
    Check if two paths refer to the same file
    Handles both absolute and relative paths
    """
    norm1 = normalize_path(path1)
    norm2 = normalize_path(path2)

    # Direct match
    if norm1 == norm2:
        return True

    # Try matching the end of the path (in case one is absolute and one is relative)
    path1_obj = Path(norm1)
    path2_obj = Path(norm2)

    # Check if they have the same name and parent directory
    try:
        return (path1_obj.name == path2_obj.name and
                path1_obj.parent.name == path2_obj.parent.name)
    except:
        return False


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

    # For file path tasks, check if paths match
    if paths_match(agent_output, expected_answer):
        return {
            "correct": True,
            "reason": "Path matches expected answer",
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


if __name__ == "__main__":
    # Test the evaluator
    test_cases = [
        ("FOUND: test_files/scenario1/setup.py", "test_files/scenario1/setup.py", True, True),
        ("test_files/scenario1/setup.py", "test_files/scenario1/setup.py", True, True),
        ("/absolute/path/setup.py", "test_files/scenario1/setup.py", True, False),
        ("", "test_files/scenario1/setup.py", True, False),
        ("wrong file", "test_files/scenario1/setup.py", True, False),
        ("any output", "test_files/scenario1/setup.py", False, False),
    ]

    print("Testing evaluator:")
    for output, expected, success, should_be_correct in test_cases:
        result = evaluate_result(output, expected, success)
        status = "✓" if result["correct"] == should_be_correct else "✗"
        print(f"{status} Output: '{output[:50]}' | Expected: {expected} | Correct: {result['correct']}")
