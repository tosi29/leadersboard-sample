"""AI Agent v1 - File search agent using Google ADK"""

import os
import sys
from pathlib import Path
from google.adk.agents.llm_agent import Agent

# Add parent directory to path to import custom tools
sys.path.insert(0, str(Path(__file__).parent.parent))
from file_search_tools import find_file, find_files_by_pattern, list_directory

# Ensure GOOGLE_API_KEY is set
if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

# Define a file search agent with custom tools
root_agent = Agent(
    model='gemini-2.0-flash',
    name='agent_v1',
    description="A file search agent that finds specific files in a directory",
    instruction="""You are a file search assistant with access to file search tools.

    Available tools:
    - find_file(filename, search_directory): Find a specific file by name
    - find_files_by_pattern(pattern, search_directory): Find files matching a glob pattern
    - list_directory(directory): List contents of a directory

    When given a task to find a file:
    1. Use the appropriate tool to search for the file
    2. The tools will return the relative path from the current working directory

    Always return your final answer in the format:
    FOUND: <path_to_file>

    For example: FOUND: test_files/scenario1/setup.py

    If you cannot find the file, return: FOUND: None
    """,
    tools=[find_file, find_files_by_pattern, list_directory],
)
