from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.os import AgentOS

load_dotenv()

hello_agent = Agent(
    name="Hello Agent",
    model=OpenAIChat(id="gpt-4o"),
    instructions="You are a helpful assistant. Keep answers short and clear.",
    markdown=True,
)

agent_os = AgentOS(
    agents=[hello_agent],
    tracing=True,
)

app = agent_os.get_app()