"""AI Agent Baseline - Simple baseline agent for comparison"""

from google.adk.agents.llm_agent import Agent

# Define a baseline agent with minimal instructions
root_agent = Agent(
    model='gemini-2.0-flash-exp',
    name='agent_baseline',
    description="A baseline file search agent with minimal configuration",
    instruction="""Find the requested file and return its path.

    Format your response as:
    FOUND: <path_to_file>
    """,
    tools=[],  # Tools will be added later
)
