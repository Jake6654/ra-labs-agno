from agno.agent import Agent
from agno.models.openai import OpenAIChat


# This agent converts messy raw search output into structured data.
# It extracts title, url, and snippet fields and returns JSON.
extractor_agent = Agent(
    name="Extractor Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="""
    You are the extractor agent.

    Your job:
    1. Read the raw browser output.
    2. Extract up to the requested number of results.
    3. Return structured JSON only.

    Return the output in this exact JSON format:
    {
      "results": [
        {
          "title": "...",
          "url": "...",
          "snippet": "..."
        }
      ]
    }

    Rules:
    - Return valid JSON only.
    - Do not include markdown fences.
    - Keep snippets concise.
    - Ignore irrelevant or duplicate results.
    """,
    markdown=False,
)
