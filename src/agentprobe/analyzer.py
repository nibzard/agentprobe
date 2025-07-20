"""Generic analysis of CLI execution traces."""

from typing import List, Dict, Any


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
        if message.get("type") == "assistant":
            analysis["total_turns"] += 1

            # Extract commands (simplified pattern matching)
            content = str(message.get("message", {}).get("content", ""))

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
    if trace and trace[-1].get("type") == "result":
        analysis["success"] = trace[-1].get("subtype") == "success"

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
