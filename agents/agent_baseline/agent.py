"""AI Agent Baseline - Simple baseline agent for comparison"""

import os
import sys
from pathlib import Path
from google.adk.agents.llm_agent import Agent

# Add parent directory to path to import custom tools
sys.path.insert(0, str(Path(__file__).parent.parent))

# Ensure GOOGLE_API_KEY is set
if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

# Define a baseline agent with file search tools
root_agent = Agent(
    model='gemini-2.5-flash',
    name='agent_baseline',
    description="A baseline file search agent with file search capability",
    instruction="""
    あなたは業務のアシスタントです。
    """,
    tools=[],
)
