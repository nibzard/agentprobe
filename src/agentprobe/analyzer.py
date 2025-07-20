"""Generic analysis of CLI execution traces."""

from typing import List, Dict, Any
from claude_code_sdk import ResultMessage


def analyze_trace(trace: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze execution trace for patterns and issues."""
    analysis = {
        "total_turns": 0,
        "commands_executed": [],
        "errors_encountered": [],
        "help_used": False,
        "success": False,
        "observations": [],
        "recommendations": [],
    }

    # Count assistant turns
    for message in trace:
        message_type = getattr(message, "type", None)
        if message_type == "assistant":
            analysis["total_turns"] += 1

            # Extract commands (simplified pattern matching)
            # Try different ways to get content from message object
            content = ""
            if hasattr(message, "message") and hasattr(message.message, "content"):
                content = str(message.message.content)
            elif hasattr(message, "content"):
                content = str(message.content)
            else:
                content = str(message)

            # Check for help usage
            if "--help" in content or "-h" in content:
                analysis["help_used"] = True
                analysis["observations"].append(
                    "Agent used help flag to understand the CLI"
                )

            # Look for error patterns
            if "error:" in content.lower() or "failed" in content.lower():
                analysis["errors_encountered"].append(content[:100] + "...")

    # Check final result
    if trace and isinstance(trace[-1], ResultMessage):
        analysis["success"] = getattr(trace[-1], "subtype", None) == "success"

    # Generate recommendations based on patterns
    if len(analysis["errors_encountered"]) > 2:
        analysis["recommendations"].append(
            "Consider improving error messages to be more actionable"
        )

    if not analysis["help_used"] and not analysis["success"]:
        analysis["recommendations"].append(
            "Agent didn't use --help flag; consider making help more discoverable"
        )

    return analysis


def aggregate_analyses(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate multiple analysis results into summary statistics."""
    if not analyses:
        return {}
    
    total_runs = len(analyses)
    success_count = sum(1 for analysis in analyses if analysis["success"])
    
    aggregate = {
        "total_runs": total_runs,
        "success_count": success_count,
        "success_rate": success_count / total_runs,
        "avg_turns": sum(analysis["total_turns"] for analysis in analyses) / total_runs,
        "min_turns": min(analysis["total_turns"] for analysis in analyses),
        "max_turns": max(analysis["total_turns"] for analysis in analyses),
        "total_errors": sum(len(analysis["errors_encountered"]) for analysis in analyses),
        "help_usage_rate": sum(1 for analysis in analyses if analysis["help_used"]) / total_runs,
        "common_observations": [],
        "common_recommendations": [],
    }
    
    # Collect unique observations and recommendations
    all_observations = []
    all_recommendations = []
    
    for analysis in analyses:
        all_observations.extend(analysis["observations"])
        all_recommendations.extend(analysis["recommendations"])
    
    # Find common patterns (appearing in multiple runs)
    from collections import Counter
    obs_counts = Counter(all_observations)
    rec_counts = Counter(all_recommendations)
    
    # Include observations/recommendations that appear in at least 20% of runs
    threshold = max(1, total_runs * 0.2)
    
    aggregate["common_observations"] = [
        obs for obs, count in obs_counts.items() if count >= threshold
    ]
    aggregate["common_recommendations"] = [
        rec for rec, count in rec_counts.items() if count >= threshold
    ]
    
    return aggregate
