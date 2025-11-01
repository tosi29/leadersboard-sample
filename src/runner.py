"""Benchmark runner - Executes agents against benchmark tasks"""

import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any
import os
from cache_manager import CacheManager


class BenchmarkRunner:
    """Runs benchmark tasks against AI agents"""

    def __init__(self, agents_dir: str = "agents", benchmarks_dir: str = "benchmarks", use_cache: bool = True):
        self.agents_dir = Path(agents_dir)
        self.benchmarks_dir = Path(benchmarks_dir)
        self.use_cache = use_cache
        self.cache_manager = CacheManager() if use_cache else None

    def load_agents(self) -> List[Path]:
        """Load all agent files from the agents directory"""
        agents = list(self.agents_dir.glob("*.py"))
        if not agents:
            raise ValueError(f"No agent files found in {self.agents_dir}")
        return agents

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
        Run an agent with a given query using adk run

        Returns:
            Dictionary with 'output', 'execution_time', 'success', and optional 'error'
        """
        start_time = time.time()

        # Get the agent file name (without .py extension)
        agent_name = agent_path.stem

        try:
            # Run the agent using subprocess with adk run
            # We pass the query via stdin
            process = subprocess.Popen(
                ["adk", "run", str(agent_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd(),
            )

            # Send the query and get the response
            stdout, stderr = process.communicate(input=query + "\n", timeout=timeout)

            execution_time = time.time() - start_time

            return {
                "output": stdout.strip(),
                "stderr": stderr.strip() if stderr else None,
                "execution_time": execution_time,
                "success": process.returncode == 0,
                "returncode": process.returncode,
            }

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            process.kill()
            return {
                "output": "",
                "execution_time": execution_time,
                "success": False,
                "error": f"Timeout after {timeout} seconds",
            }

        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "output": "",
                "execution_time": execution_time,
                "success": False,
                "error": str(e),
            }

    def run_all(self, output_file: str = "results/benchmark_results.json") -> Dict[str, Any]:
        """
        Run all agents against all benchmarks

        Returns:
            Dictionary containing all benchmark results
        """
        agents = self.load_agents()
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
                    print(f" [CACHED]")
                    print(f"    Result: {'✓ CORRECT' if task_result['correct'] else '✗ INCORRECT'} ({task_result['execution_time']:.2f}s)")
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
                    print(f"    Result: {'✓ CORRECT' if evaluation['correct'] else '✗ INCORRECT'} ({run_result['execution_time']:.2f}s)")

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
            print(f"\nCache Statistics:")
            print(f"  Cache hits: {cache_hits}/{total_tests} ({cache_hits/total_tests*100:.1f}%)")
            print(f"  New executions: {cache_misses}/{total_tests} ({cache_misses/total_tests*100:.1f}%)")

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
    args = parser.parse_args()

    use_cache = not args.no_cache

    runner = BenchmarkRunner(use_cache=use_cache)

    # Clear cache if requested
    if args.clear_cache and use_cache:
        print("Clearing cache...")
        runner.cache_manager.clear_cache()

    results = runner.run_all()

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
