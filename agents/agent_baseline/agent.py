"""AI Agent Baseline - Simple baseline agent for comparison"""

import os
from google.adk.agents.llm_agent import Agent
from google.adk.code_executors import BuiltInCodeExecutor

# Ensure GOOGLE_API_KEY is set
if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

# Define a baseline agent with code execution
root_agent = Agent(
    model='gemini-2.0-flash',  # Use gemini-2.0-flash for code execution support
    name='agent_baseline',
    description="A baseline file search agent with code execution",
    instruction="""Find the requested file using Python code and return its path.

    Format your response as:
    FOUND: <path_to_file>
    """,
    code_executor=BuiltInCodeExecutor(),
)
