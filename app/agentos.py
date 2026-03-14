from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.os import AgentOS

from app.models.schemas import SearchRequest
from app.workflows.browser_workflow import run_browser_workflow

load_dotenv()


# This function is exposed to the agent as a callable tool.
# It runs the full browser workflow and returns structured JSON.
def run_search_workflow(query: str, max_results: int = 5) -> dict:
    request = SearchRequest(query=query, max_results=max_results)
    result = run_browser_workflow(request)
    return result.model_dump()


# This UI-facing agent can trigger the workflow function.
workflow_runner_agent = Agent(
    name="Search Workflow Agent",
    model=OpenAIChat(id="gpt-4o"),
    tools=[run_search_workflow],
    instructions="""
    You are the entry agent for a multi-agent browser search workflow.

    When the user asks to search, research, compare, explain, or collect results,
    call the run_search_workflow tool.

    After calling the tool:
    - present the structured results clearly
    - mention the summary in a natural way
    - adapt the final wording to the user's query
    - do not force a ranking format unless the user explicitly requests ranking

    Keep the answer concise and useful.
    """,
    markdown=True,
)

agent_os = AgentOS(
    agents=[workflow_runner_agent],
    tracing=True,
)

app = agent_os.get_app()
