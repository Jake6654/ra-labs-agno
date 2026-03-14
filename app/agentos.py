from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.os import AgentOS

from app.models.schemas import SearchRequest
from app.workflows.browser_workflow import run_browser_workflow

load_dotenv()


# This agent is a simple UI-facing wrapper.
# It receives a user request, runs the workflow, and returns the final result.
workflow_runner_agent = Agent(
    name="Workflow Runner Agent",
    model=OpenAIChat(id="gpt-4o"),
    instructions="""
    You are the entry agent for a browser-search workflow.
    Your role is to accept a user request and explain that the workflow result
    will be returned by the backend workflow logic.
    Keep responses short.
    """,
    markdown=True,
)


# This is a simple callable wrapper you can later expose through routes or tools.
# For now, it shows how the typed request enters the workflow.
def run_search(query: str, max_results: int = 5) -> dict:
    request = SearchRequest(query=query, max_results=max_results)
    result = run_browser_workflow(request)
    return result.model_dump()


# AgentOS runtime container.
# This is what AgentOS UI connects to.
agent_os = AgentOS(
    agents=[workflow_runner_agent],
    tracing=True,
)

app = agent_os.get_app()