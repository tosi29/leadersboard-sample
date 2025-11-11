import os
import sys
from pathlib import Path

from google.adk.agents.llm_agent import Agent

# Add parent directory to path to import custom tools
sys.path.insert(0, str(Path(__file__).parent.parent))

# Ensure GOOGLE_API_KEY is set
if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

root_agent = Agent(
    model="gemini-2.5-flash",
    name="gemini_2_5_flash",
    description="Gemini 2.5 Flash",
    instruction="""
    あなたは業務のアシスタントです。
    """,
    tools=[],
)
