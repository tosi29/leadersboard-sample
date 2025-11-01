"""AI Agent v1 - File search agent using Google ADK"""

from google.adk.agents.llm_agent import Agent

# Define a simple file search agent
root_agent = Agent(
    model='gemini-2.0-flash-exp',
    name='agent_v1',
    description="A file search agent that finds specific files in a directory",
    instruction="""You are a file search assistant.
    When given a task to find a file, you should search the specified directory
    and return the full path to the file that matches the criteria.

    Always return your answer in the format:
    FOUND: <full_path_to_file>

    For example: FOUND: /path/to/setup.py
    """,
    tools=[],  # Tools will be added later
)
