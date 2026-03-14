import json
import re
import time
from dataclasses import dataclass
from typing import Any

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
def parse_json_response(raw_text: str) -> dict[str, Any]:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response: {e}")


# This helper prints simple structured logs.
def log_step(step_name: str, status: str, latency: float, extra: dict[str, Any] | None = None) -> None:
    payload = {
        "step": step_name,
        "status": status,
        "latency_sec": round(latency, 3),
    }
    if extra:
        payload.update(extra)

    print(json.dumps(payload, ensure_ascii=False))


# Represent browser-step quality explicitly so logs and behavior match reality.
@dataclass
class BrowserRunOutcome:
    raw_text: str
    status: str
    attempts: int
    query_used: str


# Detect tool-level failure traces so we do not treat them as valid search output.
def looks_like_search_failure(text: str) -> bool:
    lowered = text.lower()
    failure_markers = (
        "no results found",
        "could not run function web_search",
        "ddgsexception",
        "traceback (most recent call last):",
    )
    return any(marker in lowered for marker in failure_markers)


# lightweight signal to check whether browser content contains actual web findings.
def estimate_url_count(text: str) -> int:
    return len(re.findall(r"https?://[^\s)]+", text))


# This helper runs the browser agent with fallback queries and returns quality metadata.
def run_browser_with_fallback(request: SearchRequest, plan: PlanOutput) -> BrowserRunOutcome:
    candidate_queries = [
        plan.refined_query,
        request.query,
        f"{request.query} tools comparison",
    ]

    last_response_content = ""
    last_query_used = candidate_queries[-1]

    for idx, query in enumerate(candidate_queries, start=1):
        browser_prompt = f"""
        Search query: {query}
        Search strategy: {plan.search_strategy}
        Max results needed: {request.max_results}

        Return relevant raw findings for downstream extraction.
        """

        attempt_start = time.time()
        response = browser_agent.run(browser_prompt)
        attempt_latency = time.time() - attempt_start

        content = response.content or ""
        last_response_content = content
        last_query_used = query
        failure_trace_detected = looks_like_search_failure(content)
        url_count = estimate_url_count(content)

        # and only accept content when there is at least one URL to extract.
        if content.strip() and url_count > 0:
            attempt_status = "degraded" if failure_trace_detected else "success"
            log_step(
                "browser_attempt",
                attempt_status,
                attempt_latency,
                extra={"attempt": idx, "query_used": query, "url_count": url_count},
            )
            return BrowserRunOutcome(
                raw_text=content,
                status=attempt_status,
                attempts=idx,
                query_used=query,
            )

        log_step(
            "browser_attempt",
            "retry",
            attempt_latency,
            extra={
                "attempt": idx,
                "query_used": query,
                "url_count": url_count,
                "failure_trace_detected": failure_trace_detected,
            },
        )

    # if every attempt failed, return explicit failure metadata.
    return BrowserRunOutcome(
        raw_text=last_response_content,
        status="failure",
        attempts=len(candidate_queries),
        query_used=last_query_used,
    )


# Main workflow
def run_browser_workflow(request: SearchRequest) -> WorkflowOutput:
    workflow_start = time.time()

    if not request.query.strip():
        raise ValueError("Query cannot be empty.")

    # Step 1: Planner
    planner_start = time.time()
    planner_response = planner_agent.run(request.query)
    planner_latency = time.time() - planner_start
    log_step("planner", "success", planner_latency)

    planner_data = parse_json_response(planner_response.content)
    plan = PlanOutput(**planner_data)

    # Step 2: Browser with fallback
    browser_start = time.time()
    browser_outcome = run_browser_with_fallback(request, plan)
    browser_latency = time.time() - browser_start
    log_step(
        "browser",
        browser_outcome.status,
        browser_latency,
        extra={
            "attempts": browser_outcome.attempts,
            "query_used": browser_outcome.query_used,
        },
    )

    # stop early on hard browser failure instead of letting downstream
    # agents synthesize low-trust results from error traces.
    if browser_outcome.status == "failure":
        total_latency = time.time() - workflow_start
        fallback_output = WorkflowOutput(
            query=request.query,
            results=[],
            summary="Web search failed after multiple attempts. Please retry or adjust the query.",
        )
        log_step(
            "workflow_total",
            "failure",
            total_latency,
            extra={"result_count": 0},
        )
        return fallback_output

    # Step 3: Extractor
    extractor_prompt = f"""
    User query: {request.query}
    Max results: {request.max_results}

    Raw browser output:
    {browser_outcome.raw_text}
    """

    extractor_start = time.time()
    extractor_response = extractor_agent.run(extractor_prompt)
    extractor_latency = time.time() - extractor_start
    log_step("extractor", "success", extractor_latency)

    try:
        extractor_data = parse_json_response(extractor_response.content)
    except ValueError:
        retry_start = time.time()
        extractor_retry_response = extractor_agent.run(
            extractor_prompt + "\nReturn valid JSON only. Ignore failed tool traces."
        )
        retry_latency = time.time() - retry_start
        log_step("extractor_retry", "success", retry_latency)
        extractor_data = parse_json_response(extractor_retry_response.content)

    extracted_results = [
        SearchResult(**item) for item in extractor_data.get("results", [])
    ]

    # Step 4: Verifier
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
    
    deduped_results: list[SearchResult] = []
    seen_keys: set[str] = set()
    for item in verified_results:
        dedupe_key = (item.url or item.title).strip().lower()
        # enforce unique results and honor max_results in final output.
        if not dedupe_key or dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        deduped_results.append(item)
        if len(deduped_results) >= request.max_results:
            break

    summary = verifier_data.get("summary", "").strip()
    if browser_outcome.status == "degraded":
        summary = (
            f"{summary} Note: browser tool warnings occurred, so some results may be incomplete."
        ).strip()

    final_output = WorkflowOutput(
        query=request.query,
        results=deduped_results,
        summary=summary,
    )

    total_latency = time.time() - workflow_start
    log_step(
        "workflow_total",
        "degraded" if browser_outcome.status == "degraded" else "success",
        total_latency,
        extra={"result_count": len(final_output.results)},
    )

    return final_output
