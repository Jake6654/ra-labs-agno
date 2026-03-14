import json
import time
from typing import Any

from pydantic import ValidationError

from app.agents.planner import planner_agent
from app.agents.browser_agent import browser_agent
from app.agents.extractor import extractor_agent
from app.agents.verifier import verifier_agent
from app.models.schemas import (
    SearchRequest,
    SearchResult,
    PlanOutput,
    WorkflowOutput,
)


# This helper safely parses JSON text into a Python dictionary.
# It raises a clear error if the model returns invalid JSON.
def parse_json_response(raw_text: str) -> dict[str, Any]:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response: {e}")


# This helper prints simple structured logs.
# It helps with observability for latency and step status.
def log_step(step_name: str, status: str, latency: float, extra: dict[str, Any] | None = None) -> None:
    payload = {
        "step": step_name,
        "status": status,
        "latency_sec": round(latency, 3),
    }
    if extra:
        payload.update(extra)

    print(json.dumps(payload, ensure_ascii=False))


# This is the main workflow function.
# It coordinates planner -> browser -> extractor -> verifier.
def run_browser_workflow(request: SearchRequest) -> WorkflowOutput:
    workflow_start = time.time()

    # Basic input validation for resilience.
    # This is one of the required failure-handling cases.
    if not request.query.strip():
        raise ValueError("Query cannot be empty.")

    # ----------------------------
    # Step 1: Planner
    # ----------------------------
    planner_start = time.time()
    planner_response = planner_agent.run(request.query)
    planner_latency = time.time() - planner_start
    log_step("planner", "success", planner_latency)

    planner_data = parse_json_response(planner_response.content)
    plan = PlanOutput(**planner_data)

    # ----------------------------
    # Step 2: Browser
    # ----------------------------
    browser_prompt = f"""
    Refined query: {plan.refined_query}
    Search strategy: {plan.search_strategy}
    Max results needed: {request.max_results}
    """

    browser_start = time.time()
    browser_response = browser_agent.run(browser_prompt)
    browser_latency = time.time() - browser_start
    log_step("browser", "success", browser_latency)

    raw_browser_text = browser_response.content

    # ----------------------------
    # Step 3: Extractor
    # ----------------------------
    extractor_prompt = f"""
    User query: {request.query}
    Max results: {request.max_results}

    Raw browser output:
    {raw_browser_text}
    """

    extractor_start = time.time()
    extractor_response = extractor_agent.run(extractor_prompt)
    extractor_latency = time.time() - extractor_start
    log_step("extractor", "success", extractor_latency)

    # Retry once if extractor returns invalid JSON.
    # This is another required failure-handling example.
    try:
        extractor_data = parse_json_response(extractor_response.content)
    except ValueError:
        retry_start = time.time()
        extractor_retry_response = extractor_agent.run(extractor_prompt + "\nReturn valid JSON only.")
        retry_latency = time.time() - retry_start
        log_step("extractor_retry", "success", retry_latency)

        extractor_data = parse_json_response(extractor_retry_response.content)

    extracted_results = [
        SearchResult(**item) for item in extractor_data.get("results", [])
    ]

    # ----------------------------
    # Step 4: Verifier
    # ----------------------------
    verifier_input = {
        "query": request.query,
        "results": [result.model_dump() for result in extracted_results],
    }

    verifier_start = time.time()
    verifier_response = verifier_agent.run(json.dumps(verifier_input, ensure_ascii=False))
    verifier_latency = time.time() - verifier_start
    log_step("verifier", "success", verifier_latency)

    verifier_data = parse_json_response(verifier_response.content)

    verified_results = [
        SearchResult(**item) for item in verifier_data.get("results", [])
    ]
    summary = verifier_data.get("summary", "")

    final_output = WorkflowOutput(
        query=request.query,
        results=verified_results,
        summary=summary,
    )

    total_latency = time.time() - workflow_start
    log_step(
        "workflow_total",
        "success",
        total_latency,
        extra={"result_count": len(final_output.results)},
    )

    return final_output