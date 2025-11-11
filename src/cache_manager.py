"""Cache manager for benchmark test results"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional


class CacheManager:
    """Manages caching of benchmark test results based on file hashes"""

    def __init__(self, cache_file: str = "results/benchmark_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache_data = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Load existing cache data from file"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If cache is corrupted, start fresh
                return {"cache_version": "1.0", "cached_results": {}}
        return {"cache_version": "1.0", "cached_results": {}}

    def _save_cache(self):
        """Save cache data to file"""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache_data, f, indent=2)

    @staticmethod
    def compute_file_hash(file_path: Path) -> str:
        """
        Compute SHA256 hash of a file

        Args:
            file_path: Path to the file

        Returns:
            Hexadecimal hash string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _get_cache_key(self, agent_name: str, task_id: str) -> str:
        """Generate cache key for an agent-task combination"""
        return f"{agent_name}__{task_id}"

    def get_cached_result(
        self,
        agent_path: Path,
        benchmark: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached result if available and valid

        Args:
            agent_path: Path to the agent directory
            benchmark: Benchmark task definition

        Returns:
            Cached result if valid, None otherwise
        """
        agent_name = agent_path.name
        task_id = benchmark["id"]
        cache_key = self._get_cache_key(agent_name, task_id)

        # Check if cache entry exists
        if cache_key not in self.cache_data["cached_results"]:
            return None

        cached_entry = self.cache_data["cached_results"][cache_key]

        # Compute current hashes - hash the agent.py file
        agent_file = agent_path / "agent.py"
        agent_hash = self.compute_file_hash(agent_file)

        # For benchmark hash, we use the benchmark definition itself
        # (in case the JSON file content changes)
        benchmark_str = json.dumps(benchmark, sort_keys=True)
        benchmark_hash = hashlib.sha256(benchmark_str.encode()).hexdigest()

        # Validate hashes
        if (cached_entry.get("agent_hash") == agent_hash and
            cached_entry.get("benchmark_hash") == benchmark_hash):
            return cached_entry.get("result")

        return None

    def cache_result(
        self,
        agent_path: Path,
        benchmark: Dict[str, Any],
        result: Dict[str, Any],
        timestamp: str
    ):
        """
        Cache a test result

        Args:
            agent_path: Path to the agent directory
            benchmark: Benchmark task definition
            result: Test result to cache
            timestamp: Timestamp of the test run
        """
        agent_name = agent_path.name
        task_id = benchmark["id"]
        cache_key = self._get_cache_key(agent_name, task_id)

        # Compute hashes - hash the agent.py file
        agent_file = agent_path / "agent.py"
        agent_hash = self.compute_file_hash(agent_file)
        benchmark_str = json.dumps(benchmark, sort_keys=True)
        benchmark_hash = hashlib.sha256(benchmark_str.encode()).hexdigest()

        # Store in cache
        self.cache_data["cached_results"][cache_key] = {
            "agent_hash": agent_hash,
            "benchmark_hash": benchmark_hash,
            "result": result,
            "timestamp": timestamp,
            "agent_file": str(agent_path),
            "task_name": benchmark.get("name", task_id)
        }

        # Save to disk
        self._save_cache()

    def clear_cache(self):
        """Clear all cached results"""
        self.cache_data = {"cache_version": "1.0", "cached_results": {}}
        self._save_cache()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about cached results"""
        return {
            "total_cached": len(self.cache_data["cached_results"]),
            "cache_version": self.cache_data.get("cache_version", "unknown")
        }
