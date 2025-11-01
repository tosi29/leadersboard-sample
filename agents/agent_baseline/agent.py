"""AI Agent Baseline - Simple baseline agent for comparison"""

import os
import sys
from pathlib import Path
from google.adk.agents.llm_agent import Agent

# Add parent directory to path to import custom tools
sys.path.insert(0, str(Path(__file__).parent.parent))
from file_search_tools import find_file, find_files_by_pattern

# Ensure GOOGLE_API_KEY is set
if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

# Define a baseline agent with file search tools
root_agent = Agent(
    model='gemini-2.0-flash',
    name='agent_baseline',
    description="A baseline file search agent with file search capability",
    instruction="""Find the requested file and return its path.

    You have access to these tools:
    - find_file(filename, search_directory): Find a specific file by name
    - find_files_by_pattern(pattern, search_directory): Find files by pattern (e.g., '*.yaml')

    When looking for a file:
    - If you know the exact filename, use find_file
    - If you need to search by type (e.g., YAML file), use find_files_by_pattern

    Format your final response as:
    FOUND: <path_to_file>

    If you cannot find the file, return: FOUND: None
    """,
    tools=[find_file, find_files_by_pattern],
)
