import os
import sys
from pathlib import Path

from google.adk.agents.llm_agent import Agent
from google.adk.tools import google_search

# Add parent directory to path to import custom tools
sys.path.insert(0, str(Path(__file__).parent.parent))

# Ensure GOOGLE_API_KEY is set
if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

root_agent = Agent(
    model='gemini-2.5-flash-lite',
    name='with_google_search',
    description="検索が実行可能なエージェント",
    instruction="""
    あなたは業務のアシスタントです。
    """,
    tools=[google_search],
)
