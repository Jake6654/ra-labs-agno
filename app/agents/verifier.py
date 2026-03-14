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
    2. Remove weak or duplicate items if needed.
    3. Write a short final summary.

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
    - Keep the summary short and useful.
    - Make sure the results are relevant to the query.
    """,
    markdown=False,
)
