from pydantic import BaseModel, Field
from typing import List


# This model represents the input coming from the user.
# It defines the search query and the number of results to collect.
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User search query")
    max_results: int = Field(default=5, ge=1, le=10, description="Number of results to return")


# This model represents one structured search result.
# Each item should contain a title, url, and short snippet.
class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str


# This model represents the planner's output.
# The planner can rewrite or refine the query before the browser agent uses it.
class PlanOutput(BaseModel):
    original_query: str
    refined_query: str
    search_strategy: str


# This model represents the final workflow output.
# It combines the request, extracted results, and summary.
class WorkflowOutput(BaseModel):
    query: str
    results: List[SearchResult]
    summary: str
