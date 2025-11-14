"""Cache manager for benchmark test results stored per agent."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional


class CacheManager:
    """Reads/writes cached benchmark results for each agent."""

    CACHE_VERSION = "2.0"

    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.cache_data: Dict[str, Dict[str, Any]] = {}

    def _agent_file(self, agent_name: str) -> Path:
        return self.results_dir / f"{agent_name}.json"

    def _empty_agent_cache(self, agent_name: str) -> Dict[str, Any]:
        return {
            "agent_name": agent_name,
            "cache_version": self.CACHE_VERSION,
            "tasks": {},
            "summary": {"total": 0, "correct": 0, "incorrect": 0, "errors": 0},
            "last_updated": None,
        }

    def _load_agent_cache(self, agent_name: str) -> Dict[str, Any]:
        if agent_name in self.cache_data:
            return self.cache_data[agent_name]

        agent_file = self._agent_file(agent_name)
        if agent_file.exists():
            try:
                data = json.loads(agent_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = self._empty_agent_cache(agent_name)
        else:
            data = self._empty_agent_cache(agent_name)

        self.cache_data[agent_name] = data
        return data

    def _save_agent_cache(self, agent_name: str) -> None:
        agent_file = self._agent_file(agent_name)
        agent_file.parent.mkdir(parents=True, exist_ok=True)

        data = self.cache_data[agent_name]
        agent_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _recalculate_summary(self, agent_cache: Dict[str, Any]) -> None:
        summary = {"total": 0, "correct": 0, "incorrect": 0, "errors": 0}
        for task_entry in agent_cache.get("tasks", {}).values():
            result = task_entry.get("result", {})
            summary["total"] += 1
            if result.get("error"):
                summary["errors"] += 1
            elif result.get("correct"):
                summary["correct"] += 1
            else:
                summary["incorrect"] += 1
        agent_cache["summary"] = summary

    @staticmethod
    def compute_file_hash(file_path: Path) -> str:
        """
        Compute SHA256 hash of a file.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _get_cache_key(self, agent_name: str, task_id: str) -> str:
        return f"{agent_name}__{task_id}"

    def get_cached_result(
        self, agent_path: Path, benchmark: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Return cached task result if agent/benchmark hashes match.
        """
        agent_name = agent_path.name
        task_id = benchmark["id"]

        agent_cache = self._load_agent_cache(agent_name)
        cached_entry = agent_cache.get("tasks", {}).get(task_id)
        if not cached_entry:
            return None

        agent_file = agent_path / "agent.py"
        agent_hash = self.compute_file_hash(agent_file)

        benchmark_str = json.dumps(benchmark, sort_keys=True)
        benchmark_hash = hashlib.sha256(benchmark_str.encode()).hexdigest()

        if (
            cached_entry.get("agent_hash") == agent_hash
            and cached_entry.get("benchmark_hash") == benchmark_hash
        ):
            return cached_entry.get("result")

        return None

    def cache_result(
        self, agent_path: Path, benchmark: Dict[str, Any], result: Dict[str, Any], timestamp: str
    ) -> None:
        """
        Persist a task result for an agent.
        """
        agent_name = agent_path.name
        task_id = benchmark["id"]
        agent_cache = self._load_agent_cache(agent_name)

        agent_file = agent_path / "agent.py"
        agent_hash = self.compute_file_hash(agent_file)
        benchmark_str = json.dumps(benchmark, sort_keys=True)
        benchmark_hash = hashlib.sha256(benchmark_str.encode()).hexdigest()

        agent_cache.setdefault("tasks", {})[task_id] = {
            "task_name": benchmark.get("name", task_id),
            "agent_hash": agent_hash,
            "benchmark_hash": benchmark_hash,
            "timestamp": timestamp,
            "result": result,
        }
        agent_cache["last_updated"] = timestamp
        self._recalculate_summary(agent_cache)
        self._save_agent_cache(agent_name)

    def clear_cache(self) -> None:
        """Remove all cached agent files."""
        self.cache_data.clear()
        for json_file in self.results_dir.glob("*.json"):
            try:
                json_file.unlink()
            except OSError:
                continue

    def get_cache_stats(self) -> Dict[str, Any]:
        """Return statistics about cached results."""
        total_cached = 0
        for json_file in self.results_dir.glob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            total_cached += len(data.get("tasks", {}))

        return {
            "total_cached": total_cached,
            "cache_version": self.CACHE_VERSION,
        }
