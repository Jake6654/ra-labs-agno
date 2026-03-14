from agno.agent import Agent
from agno.models.openai import OpenAIChat


# This agent acts like a coordinator.
# It rewrites the user request into a cleaner search query
# and explains how the search should be performed.
planner_agent = Agent(
    name="Planner Agent",
    model=OpenAIChat(id="gpt-4o"),
    instructions="""
    You are the planner agent in a multi-agent workflow.

    Your job:
    1. Read the user's request.
    2. Rewrite it into a more search-friendly query.
    3. Provide a short search strategy.

    Return the output in this exact JSON format:
    {
      "original_query": "...",
      "refined_query": "...",
      "search_strategy": "..."
    }

    Rules:
    - Keep refined_query short and precise.
    - Keep search_strategy to 1 or 2 sentences.
    - Return valid JSON only.
    """,
    markdown=False,
)