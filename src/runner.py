"""Benchmark runner - Executes agents against benchmark tasks"""

import argparse
import asyncio
import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.adk.runners import InMemoryRunner
from google.genai import types

from services.cache_manager import CacheManager
from services.evaluator import evaluate_result


class BenchmarkRunner:
    """Runs benchmark tasks against AI agents"""

    def __init__(
        self,
        agents_dir: str = "agents",
        benchmarks_dir: str = "benchmarks",
        ignore_cache: bool = False,
    ):
        self.agents_dir = Path(agents_dir)
        self.benchmarks_dir = Path(benchmarks_dir)
        self.ignore_cache = ignore_cache
        self.cache_manager = CacheManager()

    def load_agents(self, selected_agent: Optional[str] = None) -> List[Path]:
        """
        Load agent directories from the agents directory.

        Args:
            selected_agent: Optional agent directory name to load. If provided,
                only the agent whose directory name matches will be returned.
        """
        # Get all directories in agents/ that contain an agent.py file
        agents = sorted(
            [d for d in self.agents_dir.iterdir() if d.is_dir() and (d / "agent.py").exists()],
            key=lambda path: path.name,
        )
        if not agents:
            raise ValueError(f"No agent directories found in {self.agents_dir}")

        if selected_agent is None:
            return agents

        agents_by_name = {agent.name: agent for agent in agents}
        if selected_agent not in agents_by_name:
            available = ", ".join(sorted(agents_by_name.keys()))
            raise ValueError(
                "Unknown agent: " + selected_agent + f". Available agents: {available}"
            )

        return [agents_by_name[selected_agent]]

    def load_benchmarks(self) -> List[Dict[str, Any]]:
        """Load all benchmark task definitions"""
        benchmarks = []
        for task_file in sorted(self.benchmarks_dir.glob("*.json")):
            with open(task_file, "r") as f:
                benchmark = json.load(f)

            # Derive an id from the filename when it is not explicitly provided.
            benchmark.setdefault("id", task_file.stem)
            benchmarks.append(benchmark)
        if not benchmarks:
            raise ValueError(f"No benchmark files found in {self.benchmarks_dir}")
        return benchmarks

    def run_agent(self, agent_path: Path, query: str, timeout: int = 60) -> Dict[str, Any]:
        """
        Run an agent with a given query using InMemoryRunner

        Returns:
            Dictionary with 'output', 'execution_time', 'success', and optional 'error'
        """
        start_time = time.time()

        # Get the agent directory name
        agent_name = agent_path.name

        try:
            # Add the agent directory to sys.path temporarily
            agent_dir_str = str(agent_path.absolute())
            if agent_dir_str not in sys.path:
                sys.path.insert(0, agent_dir_str)

            try:
                # Load the agent.py file
                spec = importlib.util.spec_from_file_location(
                    "agent_module", agent_path / "agent.py"
                )
                agent_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(agent_module)

                # Get the root_agent from the module
                root_agent = agent_module.root_agent

                # Run the agent using InMemoryRunner
                async def run_agent_async():
                    runner = InMemoryRunner(
                        app_name=agent_name,
                        agent=root_agent,
                    )

                    user_id = "test_user"
                    session_id = f"session_{agent_name}_{int(time.time())}"

                    # Create session
                    await runner.session_service.create_session(
                        app_name=agent_name,
                        user_id=user_id,
                        session_id=session_id,
                    )

                    # Run the agent
                    events = runner.run_async(
                        user_id=user_id,
                        session_id=session_id,
                        new_message=types.Content(parts=[types.Part(text=query)], role="user"),
                    )

                    # Collect all responses including code execution results
                    response_parts = []
                    debug_info = []
                    prompt_tokens = 0
                    candidates_tokens = 0

                    async for event in events:
                        # Debug: track event types
                        event_type = type(event).__name__
                        debug_info.append(f"Event: {event_type}")

                        usage_metadata = getattr(event, "usage_metadata", None)
                        if usage_metadata:
                            event_prompt_tokens = getattr(
                                usage_metadata, "prompt_token_count", None
                            )
                            if event_prompt_tokens:
                                prompt_tokens += event_prompt_tokens

                            # TODO toolUsePromptTokenCountは入力に加算？（要精査）
                            event_tool_use_prompt_tokens = getattr(
                                usage_metadata, "tool_use_prompt_token_count", None
                            )
                            if event_tool_use_prompt_tokens:
                                prompt_tokens += event_tool_use_prompt_tokens

                            event_candidates_tokens = getattr(
                                usage_metadata, "candidates_token_count", None
                            )
                            if event_candidates_tokens:
                                candidates_tokens += event_candidates_tokens

                            event_thoughts_tokens = getattr(
                                usage_metadata, "thoughts_token_count", None
                            )
                            if event_thoughts_tokens:
                                candidates_tokens += event_thoughts_tokens

                        if hasattr(event, "content") and event.content:
                            if isinstance(event.content, str):
                                response_parts.append(event.content)
                                debug_info.append("  - Added string content")
                            elif hasattr(event.content, "parts"):
                                for i, part in enumerate(event.content.parts):
                                    part_type = type(part).__name__
                                    debug_info.append(f"  - Part {i}: {part_type}")

                                    # Extract text from all part types
                                    if hasattr(part, "text") and part.text:
                                        response_parts.append(part.text)
                                        debug_info.append(f"    Added text: {part.text[:50]}...")
                                    # Extract output from code execution results
                                    elif hasattr(part, "code_execution_result"):
                                        result = part.code_execution_result
                                        if hasattr(result, "output") and result.output:
                                            response_parts.append(result.output)
                                            truncated_output = result.output[:50]
                                            debug_info.append(
                                                f"    Added code result: {truncated_output}..."
                                            )

                    # Print debug info if VERBOSE env var is set
                    if os.environ.get("VERBOSE"):
                        print("\n".join(debug_info))

                    token_usage = {
                        "prompt_token_count": prompt_tokens,
                        "candidates_token_count": candidates_tokens,
                    }

                    return "".join(response_parts), token_usage

                # Run the async function
                response, token_usage = asyncio.run(run_agent_async())

                execution_time = time.time() - start_time

                return {
                    "output": response.strip() if response else "",
                    "stderr": None,
                    "execution_time": execution_time,
                    "success": True,
                    "returncode": 0,
                    "input_tokens": token_usage.get("prompt_token_count"),
                    "output_tokens": token_usage.get("candidates_token_count"),
                }
            finally:
                # Remove from sys.path
                if agent_dir_str in sys.path:
                    sys.path.remove(agent_dir_str)

        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "output": "",
                "execution_time": execution_time,
                "success": False,
                "error": str(e),
                "input_tokens": None,
                "output_tokens": None,
            }

    def run_all(self, selected_agent: Optional[str] = None) -> Dict[str, Any]:
        """
        Run all agents against all benchmarks

        Returns:
            Dictionary containing all benchmark results
        """
        agents = self.load_agents(selected_agent)
        benchmarks = self.load_benchmarks()

        print(f"Found {len(agents)} agents and {len(benchmarks)} benchmark tasks")
        if self.cache_manager:
            cache_stats = self.cache_manager.get_cache_stats()
            if self.ignore_cache:
                print(
                    "Cache enabled (ignoring existing results): "
                    f"{cache_stats['total_cached']} cached results available"
                )
            else:
                print(f"Cache enabled: {cache_stats['total_cached']} cached results available")

        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "agents": {},
        }

        # Track cache statistics
        cache_hits = 0
        cache_misses = 0

        for agent_path in agents:
            agent_name = agent_path.stem
            print(f"\nRunning agent: {agent_name}")

            results["agents"][agent_name] = {
                "tasks": {},
                "summary": {
                    "total": 0,
                    "correct": 0,
                    "incorrect": 0,
                    "errors": 0,
                },
            }

            for benchmark in benchmarks:
                task_id = benchmark["id"]
                print(f"  Task: {task_id} - {benchmark['name']}", end="")

                # Check cache first
                cached_result = None
                if self.cache_manager and not self.ignore_cache:
                    cached_result = self.cache_manager.get_cached_result(agent_path, benchmark)

                if cached_result:
                    # Use cached result
                    task_result = cached_result
                    cache_hits += 1
                    print(" [CACHED]")
                    cached_status = "✓ CORRECT" if task_result["correct"] else "✗ INCORRECT"
                    cached_duration = task_result["execution_time"]
                    print(f"    Result: {cached_status} ({cached_duration:.2f}s)")
                else:
                    # Run the agent
                    print()  # New line for non-cached execution
                    run_result = self.run_agent(agent_path, benchmark["query"])

                    # Evaluate the result (this will be enhanced by evaluator.py)
                    evaluation = evaluate_result(
                        run_result["output"], benchmark["expected_answer"], run_result["success"]
                    )

                    # Store the result
                    task_result = {
                        "correct": evaluation["correct"],
                        "execution_time": run_result["execution_time"],
                        "agent_output": run_result["output"],
                        "expected_answer": benchmark["expected_answer"],
                        "input_tokens": run_result.get("input_tokens"),
                        "output_tokens": run_result.get("output_tokens"),
                        "error": run_result.get("error"),
                    }

                    # Cache the result
                    if self.cache_manager:
                        self.cache_manager.cache_result(
                            agent_path, benchmark, task_result, results["timestamp"]
                        )

                    cache_misses += 1
                    status = "✓ CORRECT" if evaluation["correct"] else "✗ INCORRECT"
                    duration = run_result["execution_time"]
                    print(f"    Result: {status} ({duration:.2f}s)")

                results["agents"][agent_name]["tasks"][task_id] = task_result

                # Update summary
                summary = results["agents"][agent_name]["summary"]
                summary["total"] += 1
                if task_result.get("error"):
                    summary["errors"] += 1
                elif task_result["correct"]:
                    summary["correct"] += 1
                else:
                    summary["incorrect"] += 1

        print("\nResults saved per agent under the results/ directory")

        # Print cache statistics
        if self.cache_manager:
            total_tests = cache_hits + cache_misses
            print("\nCache Statistics:")
            cache_hit_rate = (cache_hits / total_tests) * 100 if total_tests else 0.0
            cache_miss_rate = (cache_misses / total_tests) * 100 if total_tests else 0.0
            print(f"  Cache hits: {cache_hits}/{total_tests} ({cache_hit_rate:.1f}%)")
            print(f"  New executions: {cache_misses}/{total_tests} ({cache_miss_rate:.1f}%)")
            if self.ignore_cache:
                print("  Existing cached results were ignored for this run.")

        return results


def main():
    """Main entry point for the benchmark runner"""
    parser = argparse.ArgumentParser(description="Run AI agent benchmarks")
    parser.add_argument(
        "--ignore-cache",
        action="store_true",
        help="Ignore cached results and re-run all tests while still updating the cache",
    )
    parser.add_argument("--agent", help="Optional agent directory name to run (default: all)")
    args = parser.parse_args()

    runner = BenchmarkRunner(ignore_cache=args.ignore_cache)

    results = runner.run_all(selected_agent=args.agent)

    # Print summary
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)

    for agent_name, agent_data in results["agents"].items():
        summary = agent_data["summary"]
        accuracy = (summary["correct"] / summary["total"] * 100) if summary["total"] > 0 else 0

        print(f"\n{agent_name}:")
        print(f"  Total tasks: {summary['total']}")
        print(f"  Correct: {summary['correct']}")
        print(f"  Incorrect: {summary['incorrect']}")
        print(f"  Errors: {summary['errors']}")
        print(f"  Accuracy: {accuracy:.1f}%")


if __name__ == "__main__":
    main()
