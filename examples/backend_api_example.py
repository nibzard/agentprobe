"""
Example backend API implementation for AgentProbe results sharing.

This is a simplified example showing the FastAPI backend structure.
In production, this would be a separate repository/service.
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
from collections import defaultdict

# This would normally be in agentprobe.submission
from agentprobe.submission import ResultSubmission

app = FastAPI(
    title="AgentProbe Community API",
    description="Share and view AgentProbe test results",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo (use PostgreSQL in production)
results_db: List[ResultSubmission] = []
stats_cache: Dict[str, Any] = {}


class ToolStats(BaseModel):
    """Statistics for a specific tool."""
    tool: str
    total_runs: int
    success_rate: float
    avg_duration: float
    avg_cost: float
    common_friction_points: List[str]
    scenarios: Dict[str, Dict[str, Any]]


class QueryParams(BaseModel):
    """Query parameters for results."""
    tool: Optional[str] = None
    scenario: Optional[str] = None
    success: Optional[bool] = None
    limit: int = 100
    offset: int = 0


def verify_api_key(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Verify API key from Authorization header."""
    if not authorization:
        return None
    
    if authorization.startswith("Bearer "):
        return authorization.split(" ", 1)[1]
    
    return None


@app.post("/api/v1/results")
async def submit_result(
    result: ResultSubmission,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """Submit a test result."""
    # In production: validate, rate limit, store in database
    results_db.append(result)
    
    # Invalidate cache
    stats_cache.clear()
    
    return {"status": "success", "id": result.run_id}


@app.get("/api/v1/results")
async def query_results(
    tool: Optional[str] = None,
    scenario: Optional[str] = None,
    success: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0
) -> List[ResultSubmission]:
    """Query test results with filters."""
    filtered = results_db
    
    if tool:
        filtered = [r for r in filtered if r.tool == tool]
    if scenario:
        filtered = [r for r in filtered if r.scenario == scenario]
    if success is not None:
        filtered = [r for r in filtered if r.execution.success == success]
    
    # Pagination
    return filtered[offset:offset + limit]


@app.get("/api/v1/stats/tool/{tool}")
async def get_tool_stats(tool: str) -> ToolStats:
    """Get aggregated statistics for a tool."""
    cache_key = f"tool_stats_{tool}"
    
    if cache_key in stats_cache:
        return stats_cache[cache_key]
    
    # Calculate stats
    tool_results = [r for r in results_db if r.tool == tool]
    
    if not tool_results:
        raise HTTPException(404, f"No results found for tool: {tool}")
    
    # Aggregate by scenario
    scenarios = defaultdict(lambda: {"runs": 0, "successes": 0, "durations": []})
    friction_counts = defaultdict(int)
    
    for result in tool_results:
        scenario_stats = scenarios[result.scenario]
        scenario_stats["runs"] += 1
        if result.execution.success:
            scenario_stats["successes"] += 1
        scenario_stats["durations"].append(result.execution.duration)
        
        # Count friction points
        for friction in result.analysis.friction_points:
            friction_counts[friction] += 1
    
    # Calculate scenario stats
    scenario_data = {}
    for scenario, stats in scenarios.items():
        scenario_data[scenario] = {
            "total_runs": stats["runs"],
            "success_rate": stats["successes"] / stats["runs"] if stats["runs"] > 0 else 0,
            "avg_duration": sum(stats["durations"]) / len(stats["durations"]) if stats["durations"] else 0
        }
    
    # Get top friction points
    top_friction = sorted(friction_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Overall stats
    total_runs = len(tool_results)
    successful_runs = sum(1 for r in tool_results if r.execution.success)
    all_durations = [r.execution.duration for r in tool_results]
    
    stats = ToolStats(
        tool=tool,
        total_runs=total_runs,
        success_rate=successful_runs / total_runs if total_runs > 0 else 0,
        avg_duration=sum(all_durations) / len(all_durations) if all_durations else 0,
        avg_cost=0.0,  # Calculate from cost data
        common_friction_points=[f[0] for f in top_friction],
        scenarios=scenario_data
    )
    
    # Cache for 5 minutes
    stats_cache[cache_key] = stats
    
    return stats


@app.get("/api/v1/stats/scenario/{tool}/{scenario}")
async def get_scenario_stats(tool: str, scenario: str):
    """Get detailed statistics for a specific scenario."""
    results = [
        r for r in results_db 
        if r.tool == tool and r.scenario == scenario
    ]
    
    if not results:
        raise HTTPException(404, f"No results found for {tool}/{scenario}")
    
    # Recent results
    recent = sorted(results, key=lambda x: x.timestamp, reverse=True)[:10]
    
    # Error patterns
    errors = defaultdict(int)
    for r in results:
        if not r.execution.success and r.execution.error_message:
            errors[r.execution.error_message] += 1
    
    return {
        "tool": tool,
        "scenario": scenario,
        "total_runs": len(results),
        "success_rate": sum(1 for r in results if r.execution.success) / len(results),
        "recent_results": recent,
        "common_errors": dict(sorted(errors.items(), key=lambda x: x[1], reverse=True)[:5])
    }


@app.get("/api/v1/leaderboard")
async def get_leaderboard():
    """Get success rate leaderboard across all tools."""
    tool_scores = defaultdict(lambda: {"runs": 0, "successes": 0})
    
    for result in results_db:
        tool_scores[result.tool]["runs"] += 1
        if result.execution.success:
            tool_scores[result.tool]["successes"] += 1
    
    # Calculate success rates
    leaderboard = []
    for tool, scores in tool_scores.items():
        if scores["runs"] > 0:
            leaderboard.append({
                "tool": tool,
                "success_rate": scores["successes"] / scores["runs"],
                "total_runs": scores["runs"]
            })
    
    # Sort by success rate
    leaderboard.sort(key=lambda x: x["success_rate"], reverse=True)
    
    return leaderboard


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "AgentProbe Community API",
        "version": "1.0.0",
        "endpoints": {
            "submit_result": "/api/v1/results",
            "query_results": "/api/v1/results",
            "tool_stats": "/api/v1/stats/tool/{tool}",
            "scenario_stats": "/api/v1/stats/scenario/{tool}/{scenario}",
            "leaderboard": "/api/v1/leaderboard"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)