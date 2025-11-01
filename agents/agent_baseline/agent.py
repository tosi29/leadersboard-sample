"""AI Agent Baseline - Simple baseline agent for comparison"""

import os
import sys
from pathlib import Path
from google.adk.agents.llm_agent import Agent

# Add parent directory to path to import custom tools
sys.path.insert(0, str(Path(__file__).parent.parent))
from file_search_tools import find_file

# Ensure GOOGLE_API_KEY is set
if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

# Define a baseline agent with minimal tools
root_agent = Agent(
    model='gemini-2.0-flash',
    name='agent_baseline',
    description="A baseline file search agent with basic file search capability",
    instruction="""Find the requested file and return its path.

    You have access to the find_file tool:
    - find_file(filename, search_directory): Find a file by name in a directory

    Format your final response as:
    FOUND: <path_to_file>

    If you cannot find the file, return: FOUND: None
    """,
    tools=[find_file],
)
