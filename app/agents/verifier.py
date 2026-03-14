from agno.agent import Agent
from agno.models.openai import OpenAIChat


# This agent checks quality and consistency.
# It validates the extracted results and produces a final summary.
verifier_agent = Agent(
    name="Verifier Agent",
    model=OpenAIChat(id="gpt-5.4"),
    instructions="""
    You are the verifier agent.

    Your job:
    1. Review the extracted search results.
    2. Remove weak, duplicate, or irrelevant items if needed.
    3. Write a short final summary that matches the user's query intent.

    Return the output in this exact JSON format:
    {
      "results": [
        {
          "title": "...",
          "url": "...",
          "snippet": "..."
        }
      ],
      "summary": "..."
    }

    Rules:
    - Return valid JSON only.
    - Do not include markdown fences.
    - Keep the summary short, useful, and query-aware.
    - Make sure the results are relevant to the user's query.
    - Remove weak or duplicate results when appropriate.
    - Do not force a ranking unless the user explicitly asks for ranked output.
    - If the user asks for explanations, suggestions, comparisons, or definitions, adapt the summary naturally.
    """,
    markdown=False,
)
