from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools


# This agent gathers raw information from the web.
# It uses a search tool to find candidate results related to the refined query.
browser_agent = Agent(
    name="Browser Agent",
    model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGoTools()],
    instructions="""
    You are the browser agent.

    Your job:
    1. Search the web using the given refined query.
    2. Collect relevant candidate results.
    3. Return raw findings that can later be cleaned by the extractor.

    Rules:
    - Focus on relevance.
    - Prefer trustworthy sources.
    - Return enough information for downstream extraction.
    """,
    markdown=True,
)