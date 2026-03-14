# AI-Native Multi-Agent Browser Search Workflow with Agno

A practical multi-agent workflow built with Agno and AgentOS that takes a user search request, plans a search strategy, gathers raw web information, extracts structured results, verifies quality, and returns a concise final summary.

This project was built for the **Option A — Browser Automation Multi-Agent** track. The system completes a browser-like research task on public web sources and returns **structured JSON output**, matching the assignment goal of a runnable end-to-end multi-agent workflow. 

## Why this track

I chose **Option A — Browser Automation Multi-Agent** because it maps naturally to a realistic multi-agent decomposition:

- a planner to refine the search request
- a browser/search agent to gather candidate information
- an extractor to structure raw findings
- a verifier to clean results and produce the final summary

This made it possible to demonstrate:
- real agent coordination
- typed handoffs
- resilience through retries/fallbacks
- observability with step-by-step logging
- a clear AgentOS UI demo

## Architecture

### High-level workflow

```text
User Query
   ↓
Planner Agent
   ↓
Browser Agent
   ↓
Extractor Agent
   ↓
Verifier Agent
   ↓
Structured JSON Output
```
## Agent Roles

### Planner Agent

The Planner Agent receives the original user query and rewrites it into a refined search query.  
It also produces a short search strategy that guides the browser agent.

Responsibilities:

- normalize or clarify the user query
- produce a refined search query
- define a search strategy for downstream agents

Example output:

```json
{
  "original_query": "top AI coding tools",
  "refined_query": "top AI coding assistants for developers comparison",
  "search_strategy": "focus on comparison articles and official product pages"
}
```
### Browser Agent

The Browser Agent performs the information gathering stage.

It uses a web search tool to retrieve candidate information from public web sources using the refined query from the planner.

Responsibilities:

- execute web searches
- collect raw findings
- return unstructured search results

The output from this step is intentionally raw and noisy, because the extractor agent will clean and structure the data.

### Extractor Agent

The Extractor Agent converts the raw browser findings into structured data that downstream agents can process.

Because the browser agent returns noisy and unstructured text, this step extracts the most relevant information and formats it into a clean schema.

Responsibilities:

- extract structured information from raw search results
- identify relevant titles, URLs, and short descriptions
- convert noisy text into structured objects
- prepare results for verification and summarization

Example output:

```json
{
  "title": "...",
  "url": "...",
  "snippet": "..."
}
```

### Verifier Agent

The Verifier Agent performs the final quality control step before the response is returned to the user.

It receives the structured results produced by the extractor agent and ensures that the results are relevant, non-duplicated, and suitable for summarization.

Responsibilities:

- remove weak or irrelevant results
- deduplicate similar entries
- ensure results match the user query
- produce a concise final summary

Example output:

```json
{
  "results": [
    {
      "title": "Real Python",
      "url": "https://realpython.com",
      "snippet": "A popular platform offering modern Python tutorials and practical examples."
    }
  ],
  "summary": "Real Python and similar learning platforms provide beginner-friendly Python tutorials and practical exercises for new developers."
}
```
The verifier ensures the final response is clean, relevant, and safe to present to the user.

### Data Flow and Typed Handoffs
Each agent communicates using structured data models.
This reduces ambiguity between agents and simplifies downstream processing.

Key schemas used in the workflow:
### SearchRequest
```json
{
  "query": "user search query",
  "max_results": 5
}
```
### SearchResult
```json
{
  "title": "result title",
  "url": "source url",
  "snippet": "short summary of the content"
}
```
### WorkflowOutput
```json
{
  "query": "original user query",
  "results": [ ... ],
  "summary": "final summary"
}
```
Using typed schemas ensures that each stage of the pipeline produces predictable outputs for the next agent.

### Resilience and Fallbacks
Web search can fail due to network issues, tool errors, or low-quality search results.

To improve reliability, the workflow includes several fallback mechanisms:

- multiple search query attempts
- alternative query variants
- retry logic when parsing invalid JSON
- graceful failure handling when no results are available

Example fallback search sequence:
```text
1. refined query from planner
2. original user query
3. query + "overview"
```
If the browser step fails completely, the workflow returns a controlled fallback message instead of crashing.

### Observability

Each step of the workflow logs structured events for debugging and observability.

Example step log:
```json
{
  "step": "browser",
  "status": "success",
  "latency_sec": 24.3,
  "attempts": 1
}
```
This makes it easier to inspect agent behavior and diagnose issues during development.

Key logged stages include:
- planner execution
- browser search attempts
- extractor parsing
- verifier validation
- total workflow latency
  
## Running the Project
### Python Virtual Environment
```
python3 -m venv .venv
source .venv/bin/activate
```
### Install dependencies
```
pip install -r requirements.txt
```
### Set environment variables
```
OPENAI_API_KEY=your_api_key_here
```
Start AgentOS
```
fastapi dev app/agentos.py
```
Then open the AgentOS dashboard in your browser to interact with the agent.
### Example Queries
Example prompts that work well with this systems:
```
- Find the best beginner-friendly Python learning resources.

- Compare GitHub Copilot and Cursor for everyday development.

- Explain the difference between an AI coding assistant and an AI agent.

- Find trustworthy sources about AI coding assistants.

```
### Example Output
Example structured workflow output:
``` json
{
  "query": "beginner python resources",
  "results": [
    {
      "title": "Real Python",
      "url": "https://realpython.com",
      "snippet": "Comprehensive Python tutorials and practical coding examples."
    },
    {
      "title": "Automate the Boring Stuff with Python",
      "url": "https://automatetheboringstuff.com",
      "snippet": "A project-based book teaching Python through practical automation tasks."
    }
  ],
  "summary": "Beginner Python learners often benefit from a mix of structured courses and project-based learning resources."
}
```
## Design Decisions

### Query-Aware Response Generation

The system adapts its responses based on the user’s query and intent.

Rather than enforcing a fixed output style, the workflow produces responses that are appropriate for the type of question being asked. Some queries may require structured results from multiple sources, while others benefit from concise explanations or summaries.

Examples of response styles include:

- returning relevant resources when the user is searching for information
- producing concise summaries when the user asks for explanations
- highlighting key differences when the user asks for comparisons

This approach keeps the system flexible and allows the agents to produce responses that better match the user's needs.

## Limitations and Reflections

While the multi-agent architecture improves modularity and observability, it does not always guarantee better performance.

One practical observation from building this system is that multi-agent workflows introduce additional latency. Even for relatively simple questions, the query must pass through multiple stages (planner → browser → extractor → verifier), which increases the total response time.

For example, a simple explanatory query may still trigger the full pipeline, even though a direct answer could be generated more efficiently with fewer steps.

Because of this, increasing the number of agents does not necessarily lead to better results. In real production systems, it is often more effective to:

- clearly define the responsibility of each agent
- minimize unnecessary agent hops
- keep the workflow as simple as possible

A carefully designed set of agents with well-defined roles is typically more efficient than a large number of loosely coordinated agents.






