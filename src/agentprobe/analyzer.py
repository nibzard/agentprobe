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
        message_class = type(message).__name__
        
        # Debug: Track all message types we see
        if message_type not in [None, "human"]:  # Skip common non-assistant types
            analysis["observations"].append(f"Debug: Found {message_class} with type='{message_type}'")
        
        # Count various types of assistant interactions
        if (message_type == "assistant" or 
            message_class in ["AssistantMessage", "TextMessage"] or
            (hasattr(message, "role") and getattr(message, "role") == "assistant")):
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


async def enhanced_analyze_trace(
    trace: List[Dict[str, Any]], 
    scenario_text: str = "", 
    tool_name: str = ""
) -> Dict[str, Any]:
    """Enhanced analysis combining traditional patterns with LLM insights."""
    
    # Start with traditional analysis
    traditional_analysis = analyze_trace(trace)
    
    # Add Claude CLI analysis if scenario info is available
    if scenario_text and tool_name:
        try:
            claude_analysis = await claude_analyze_trace(trace, scenario_text, tool_name)
            
            # Merge analyses
            enhanced_analysis = traditional_analysis.copy()
            
            # Override success if Claude detected discrepancy
            if claude_analysis.get("discrepancy"):
                enhanced_analysis["success"] = claude_analysis.get("actual_success", False)
                enhanced_analysis["observations"].append(
                    "⚠️ Claude detected discrepancy between claimed and actual success"
                )
            
            # Add Claude-detected failure reasons
            if claude_analysis.get("failure_reasons"):
                enhanced_analysis["observations"].extend([
                    f"🔍 Claude Analysis: {reason}" for reason in claude_analysis["failure_reasons"]
                ])
            
            # Add evidence summary
            if claude_analysis.get("evidence_summary"):
                enhanced_analysis["observations"].append(
                    f"📋 Evidence: {claude_analysis['evidence_summary']}"
                )
            
            # Store Claude analysis for reporting
            enhanced_analysis["llm_analysis"] = claude_analysis
            
            return enhanced_analysis
            
        except Exception as e:
            # Fall back to traditional analysis if Claude CLI fails
            traditional_analysis["observations"].append(
                f"⚠️ Claude CLI analysis failed: {str(e)}"
            )
            return traditional_analysis
    
    return traditional_analysis


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


async def claude_analyze_trace(
    trace: List[Dict[str, Any]], 
    scenario_text: str, 
    tool_name: str
) -> Dict[str, Any]:
    """Use Claude CLI to analyze trace for better success/failure detection."""
    import subprocess
    
    # Format trace for analysis
    trace_summary = []
    for i, message in enumerate(trace, 1):
        message_class = type(message).__name__
        
        # Extract content in a readable format
        content = ""
        if hasattr(message, "content"):
            content = str(message.content)[:300]  # Limit length
        elif hasattr(message, "result"):
            content = str(getattr(message, "result", ""))[:300]
        else:
            content = str(message)[:300]
            
        trace_summary.append(f"{i}. [{message_class}] {content}")
    
    # Create analysis prompt
    analysis_prompt = f"""Analyze this CLI interaction trace. An AI agent was asked to: "{scenario_text}"

Tool being tested: {tool_name}

Interaction trace:
{chr(10).join(trace_summary)}

Did the task actually complete successfully? Look for:
- Permission denials or access issues that were ignored
- Claims of success without supporting evidence  
- Tool failures that the agent didn't handle properly

Respond with a brief analysis including:
1. Whether the task truly succeeded
2. Any discrepancies between claimed vs actual success
3. Specific failure reasons if applicable
4. Recommendations for the CLI tool"""

    try:
        # Use Claude CLI to analyze
        result = subprocess.run(
            ["claude", "--no-prompt", analysis_prompt],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            claude_response = result.stdout.strip()
            
            # Parse Claude's response for key insights
            response_lower = claude_response.lower()
            
            # Simple pattern detection in Claude's response
            actual_success = None
            if "did not actually succeed" in response_lower or "task failed" in response_lower:
                actual_success = False
            elif "task succeeded" in response_lower or "completed successfully" in response_lower:
                actual_success = True
                
            # Check for discrepancy mentions
            discrepancy = "discrepancy" in response_lower or "false positive" in response_lower
            
            # Extract failure reasons (simple heuristic)
            failure_reasons = []
            if "permission denied" in response_lower:
                failure_reasons.append("Permission denied")
            if "not authenticated" in response_lower:
                failure_reasons.append("Authentication required")
                
            return {
                "actual_success": actual_success,
                "discrepancy": discrepancy,
                "failure_reasons": failure_reasons,
                "evidence_summary": claude_response[:200] + "..." if len(claude_response) > 200 else claude_response,
                "claude_analysis": claude_response
            }
        else:
            # Fallback if Claude CLI fails
            return {"error": f"Claude CLI failed: {result.stderr}"}
            
    except Exception as e:
        # Fallback to basic pattern detection
        trace_text = " ".join(trace_summary).lower()
        
        actual_success = None
        failure_reasons = []
        
        if "claude requested permissions" in trace_text or "haven't granted" in trace_text:
            actual_success = False
            failure_reasons.append("Permission denied - agent couldn't perform required actions")
        
        return {
            "actual_success": actual_success,
            "discrepancy": False,
            "failure_reasons": failure_reasons,
            "evidence_summary": f"Fallback analysis - Claude CLI unavailable: {str(e)}"
        }
