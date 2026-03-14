# This file is a simple local test runner for the workflow.
# It allows us to run the workflow without using AgentOS UI.

import os
import json

from dotenv import load_dotenv

from app.models.schemas import SearchRequest
from app.workflows.browser_workflow import run_browser_workflow


def main() -> None:
    # Load local environment variables from .env for OpenAI auth.
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to .env or export it in your shell.")

    # Create a request object using the typed schema.
    request = SearchRequest(
        query="top AI coding tools for developers",
        max_results=5,
    )

    # Run the workflow pipeline.
    result = run_browser_workflow(request)

    # Print the structured output.
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
