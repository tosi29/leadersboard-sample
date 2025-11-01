"""AI Agent v1 - File search agent using Google ADK"""

import os
from google.adk.agents.llm_agent import Agent
from google.adk.code_executors import BuiltInCodeExecutor

# Ensure GOOGLE_API_KEY is set
if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

# Define a file search agent with code execution capabilities
root_agent = Agent(
    model='gemini-2.0-flash',  # Use gemini-2.0-flash for code execution support
    name='agent_v1',
    description="A file search agent that finds specific files in a directory",
    instruction="""You are a file search assistant with code execution capabilities.
    When given a task to find a file, you can write and execute Python code to search the filesystem.

    Use Python code to:
    - List directories with os.listdir() or pathlib.Path().glob()
    - Find files matching specific patterns
    - Return the full path to the file

    Always return your final answer in the format:
    FOUND: <full_path_to_file>

    For example: FOUND: test_files/scenario1/setup.py
    """,
    code_executor=BuiltInCodeExecutor(),
)
