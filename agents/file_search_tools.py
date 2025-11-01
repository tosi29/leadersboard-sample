"""Custom tools for file search operations

These tools allow agents to search the local filesystem.
"""

import os
from pathlib import Path
from typing import Optional, List


def find_file(filename: str, search_directory: str = ".") -> Optional[str]:
    """
    Search for a file by name in a directory and its subdirectories.

    Args:
        filename: The name of the file to find (e.g., 'setup.py')
        search_directory: The directory to search in (default: current directory)

    Returns:
        The relative path to the file if found, None otherwise

    Example:
        >>> find_file("setup.py", "test_files/scenario1")
        "test_files/scenario1/setup.py"
    """
    # Convert to absolute path
    base_path = Path(search_directory).resolve()

    # Check if directory exists
    if not base_path.exists():
        return None

    # Search for the file
    for root, dirs, files in os.walk(base_path):
        if filename in files:
            full_path = Path(root) / filename
            # Return relative path from current working directory
            try:
                return str(full_path.relative_to(Path.cwd()))
            except ValueError:
                # If can't get relative path, return absolute
                return str(full_path)

    return None


def find_files_by_pattern(pattern: str, search_directory: str = ".") -> List[str]:
    """
    Search for files matching a glob pattern.

    Args:
        pattern: Glob pattern to match (e.g., '*.yaml', 'config.*')
        search_directory: The directory to search in (default: current directory)

    Returns:
        List of relative paths to matching files

    Example:
        >>> find_files_by_pattern("*.yaml", "test_files/scenario1")
        ["test_files/scenario1/config/config.yaml"]
    """
    base_path = Path(search_directory).resolve()

    if not base_path.exists():
        return []

    # Use rglob for recursive search
    matches = []
    for file_path in base_path.rglob(pattern):
        if file_path.is_file():
            try:
                rel_path = str(file_path.relative_to(Path.cwd()))
            except ValueError:
                rel_path = str(file_path)
            matches.append(rel_path)

    return matches


def list_directory(directory: str = ".") -> List[str]:
    """
    List contents of a directory.

    Args:
        directory: The directory to list (default: current directory)

    Returns:
        List of file and directory names in the directory

    Example:
        >>> list_directory("test_files/scenario1")
        ["setup.py", "README.md", "src", "config"]
    """
    dir_path = Path(directory).resolve()

    if not dir_path.exists() or not dir_path.is_dir():
        return []

    return [item.name for item in dir_path.iterdir()]
