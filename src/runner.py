"""Benchmark runner - Executes agents against benchmark tasks"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from cache_manager import CacheManager


class BenchmarkRunner:
    """Runs benchmark tasks against AI agents"""

    def __init__(
        self,
        agents_dir: str = "agents",
        benchmarks_dir: str = "benchmarks",
        use_cache: bool = True,
    ):
        self.agents_dir = Path(agents_dir)
        self.benchmarks_dir = Path(benchmarks_dir)
        self.use_cache = use_cache
        self.cache_manager = CacheManager() if use_cache else None

    def load_agents(self, selected_agent: Optional[str] = None) -> List[Path]:
        """
        Load agent directories from the agents directory.

        Args:
            selected_agent: Optional agent directory name to load. If provided,
                only the agent whose directory name matches will be returned.
        """
        # Get all directories in agents/ that contain an agent.py file
        agents = sorted(
            [
                d
                for d in self.agents_dir.iterdir()
                if d.is_dir() and (d / "agent.py").exists()
            ],
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
                "Unknown agent: "
                + selected_agent
                + f". Available agents: {available}"
            )

        return [agents_by_name[selected_agent]]

    def load_benchmarks(self) -> List[Dict[str, Any]]:
        """Load all benchmark task definitions"""
        benchmarks = []
        for task_file in sorted(self.benchmarks_dir.glob("*.json")):
            with open(task_file, 'r') as f:
                benchmarks.append(json.load(f))
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
            # Import required modules
            import asyncio
            import importlib.util
            import sys

            from google.adk.runners import InMemoryRunner
            from google.genai import types

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

                    async for event in events:
                        # Debug: track event types
                        event_type = type(event).__name__
                        debug_info.append(f"Event: {event_type}")

                        if hasattr(event, 'content') and event.content:
                            if isinstance(event.content, str):
                                response_parts.append(event.content)
                                debug_info.append("  - Added string content")
                            elif hasattr(event.content, 'parts'):
                                for i, part in enumerate(event.content.parts):
                                    part_type = type(part).__name__
                                    debug_info.append(f"  - Part {i}: {part_type}")

                                    # Extract text from all part types
                                    if hasattr(part, 'text') and part.text:
                                        response_parts.append(part.text)
                                        debug_info.append(f"    Added text: {part.text[:50]}...")
                                    # Extract output from code execution results
                                    elif hasattr(part, 'code_execution_result'):
                                        result = part.code_execution_result
                                        if hasattr(result, 'output') and result.output:
                                            response_parts.append(result.output)
                                            truncated_output = result.output[:50]
                                            debug_info.append(
                                                f"    Added code result: {truncated_output}..."
                                            )

                    # Print debug info if VERBOSE env var is set
                    if os.environ.get('VERBOSE'):
                        print("\n".join(debug_info))

                    return "".join(response_parts)

                # Run the async function
                response = asyncio.run(run_agent_async())

                execution_time = time.time() - start_time

                return {
                    "output": response.strip() if response else "",
                    "stderr": None,
                    "execution_time": execution_time,
                    "success": True,
                    "returncode": 0,
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
            }

    def run_all(
        self,
        output_file: str = "results/benchmark_results.json",
        selected_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run all agents against all benchmarks

        Returns:
            Dictionary containing all benchmark results
        """
        agents = self.load_agents(selected_agent)
        benchmarks = self.load_benchmarks()

        print(f"Found {len(agents)} agents and {len(benchmarks)} benchmark tasks")
        if self.use_cache:
            cache_stats = self.cache_manager.get_cache_stats()
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
                }
            }

            for benchmark in benchmarks:
                task_id = benchmark["id"]
                print(f"  Task: {task_id} - {benchmark['name']}", end="")

                # Check cache first
                cached_result = None
                if self.use_cache:
                    cached_result = self.cache_manager.get_cached_result(agent_path, benchmark)

                if cached_result:
                    # Use cached result
                    task_result = cached_result
                    cache_hits += 1
                    print(" [CACHED]")
                    cached_status = (
                        "✓ CORRECT" if task_result["correct"] else "✗ INCORRECT"
                    )
                    cached_duration = task_result["execution_time"]
                    print(f"    Result: {cached_status} ({cached_duration:.2f}s)")
                else:
                    # Run the agent
                    print()  # New line for non-cached execution
                    run_result = self.run_agent(agent_path, benchmark["query"])

                    # Evaluate the result (this will be enhanced by evaluator.py)
                    from evaluator import evaluate_result
                    evaluation = evaluate_result(
                        run_result["output"],
                        benchmark["expected_answer"],
                        run_result["success"]
                    )

                    # Store the result
                    task_result = {
                        "task_id": task_id,
                        "task_name": benchmark["name"],
                        "correct": evaluation["correct"],
                        "execution_time": run_result["execution_time"],
                        "agent_output": run_result["output"][:500],  # Truncate for storage
                        "expected_answer": benchmark["expected_answer"],
                        "token_count": None,  # Placeholder for future implementation
                        "error": run_result.get("error"),
                    }

                    # Cache the result
                    if self.use_cache:
                        self.cache_manager.cache_result(
                            agent_path,
                            benchmark,
                            task_result,
                            results["timestamp"]
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

        # Save results to file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\nResults saved to {output_file}")

        # Print cache statistics
        if self.use_cache:
            total_tests = cache_hits + cache_misses
            print("\nCache Statistics:")
            cache_hit_rate = (cache_hits / total_tests) * 100 if total_tests else 0.0
            cache_miss_rate = (cache_misses / total_tests) * 100 if total_tests else 0.0
            print(f"  Cache hits: {cache_hits}/{total_tests} ({cache_hit_rate:.1f}%)")
            print(
                f"  New executions: {cache_misses}/{total_tests} ({cache_miss_rate:.1f}%)"
            )

        return results


def main():
    """Main entry point for the benchmark runner"""
    import argparse

    parser = argparse.ArgumentParser(description="Run AI agent benchmarks")
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching and run all tests (default: use cache)"
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear cache before running tests"
    )
    parser.add_argument(
        "--agent",
        help="Optional agent directory name to run (default: all)"
    )
    args = parser.parse_args()

    use_cache = not args.no_cache

    runner = BenchmarkRunner(use_cache=use_cache)

    # Clear cache if requested
    if args.clear_cache and use_cache:
        print("Clearing cache...")
        runner.cache_manager.clear_cache()

    results = runner.run_all(selected_agent=args.agent)

    # Print summary
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)

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
