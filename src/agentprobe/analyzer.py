"""Generic analysis of CLI execution traces."""

from typing import List, Dict, Any
from claude_code_sdk import ResultMessage, query, ClaudeCodeOptions


def analyze_trace(trace: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Basic trace metrics collection - intelligence comes from Claude CLI analysis."""
    analysis = {
        "total_turns": 0,
        "success": False,
        "observations": [],
        "recommendations": [],
        "trace_length": len(trace),
    }

    # Count assistant turns only
    for message in trace:
        message_type = getattr(message, "type", None)
        message_class = type(message).__name__
        
        # Count various types of assistant interactions
        if (message_type == "assistant" or 
            message_class in ["AssistantMessage", "TextMessage"] or
            (hasattr(message, "role") and getattr(message, "role") == "assistant")):
            analysis["total_turns"] += 1

    # Check final result from SDK
    if trace and isinstance(trace[-1], ResultMessage):
        analysis["success"] = getattr(trace[-1], "subtype", None) == "success"

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
            claude_analysis = await claude_analyze_trace(
                trace, scenario_text, tool_name, 
                claimed_success=traditional_analysis["success"]
            )
            
            # Merge analyses
            enhanced_analysis = traditional_analysis.copy()
            
            # Override success if Claude detected discrepancy
            if claude_analysis.get("discrepancy"):
                enhanced_analysis["success"] = claude_analysis.get("actual_success", False)
                enhanced_analysis["observations"].append(
                    "⚠️ Claude detected discrepancy between claimed and actual success"
                )
            
            # Use Claude's insights to populate all fields
            if claude_analysis.get("failure_reasons"):
                enhanced_analysis["observations"].extend([
                    f"🔍 Claude Analysis: {reason}" for reason in claude_analysis["failure_reasons"]
                ])
            
            # Add Claude's recommendations
            if claude_analysis.get("recommendations"):
                enhanced_analysis["recommendations"].extend(claude_analysis["recommendations"])
            
            # Add help usage insight from Claude
            if claude_analysis.get("help_used") is not None:
                if claude_analysis["help_used"]:
                    enhanced_analysis["observations"].append("🔍 Claude detected agent used help flags appropriately")
                else:
                    enhanced_analysis["observations"].append("🔍 Claude noted agent did not use help flags")
            
            # Add Claude's full analysis as evidence
            if claude_analysis.get("claude_analysis"):
                enhanced_analysis["observations"].append(
                    f"📋 Full Claude Analysis: {claude_analysis['claude_analysis'][:500]}..."
                )
            
            # Note if fallback was used
            if claude_analysis.get("fallback_used"):
                enhanced_analysis["observations"].append(
                    "⚠️ Using fallback analysis (Claude Code SDK error)"
                )
            
            # Store Claude analysis for reporting
            enhanced_analysis["llm_analysis"] = claude_analysis
            
            return enhanced_analysis
            
        except Exception as e:
            # Fall back to traditional analysis if Claude Code SDK fails
            traditional_analysis["observations"].append(
                f"⚠️ Claude Code SDK analysis failed: {str(e)}"
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
        "total_issues": sum(len(analysis.get("llm_analysis", {}).get("failure_reasons", [])) for analysis in analyses),
        "help_usage_rate": sum(1 for analysis in analyses if analysis.get("llm_analysis", {}).get("help_used", False)) / total_runs,
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
    tool_name: str,
    claimed_success: bool = None
) -> Dict[str, Any]:
    """Use Claude Code SDK to analyze trace for better success/failure detection."""
    
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
    
    # Create comprehensive analysis prompt
    analysis_prompt = f"""Analyze this CLI interaction trace. An AI agent was asked to: "{scenario_text}"

Tool being tested: {tool_name}

Interaction trace:
{chr(10).join(trace_summary)}

Provide a comprehensive analysis covering:

1. SUCCESS ASSESSMENT:
   - Did the task actually complete successfully based on evidence?
   - Are there discrepancies between claimed success and actual results?
   - Look for permission denials, authentication failures, or tool errors that were ignored

2. AGENT BEHAVIOR ANALYSIS:
   - Did the agent use help flags (--help, -h) appropriately?
   - How did the agent handle errors or obstacles?
   - Were there any missed opportunities for better CLI usage?

3. CLI USABILITY INSIGHTS:
   - What makes this CLI easy/difficult for AI agents to use?
   - Are error messages clear and actionable?
   - Is help documentation discoverable and useful?

4. SPECIFIC ISSUES:
   - List any permission denials, authentication problems, or tool failures
   - Identify false positive scenarios where success was claimed incorrectly
   - Note any CLI design issues that caused problems

5. RECOMMENDATIONS:
   - Suggest improvements for CLI usability with AI agents
   - Recommend better error handling or documentation

Be thorough and specific in your analysis."""

    try:
        # Use Claude Code SDK for analysis (same as scenario execution)
        options = ClaudeCodeOptions(max_turns=1)  # Single analysis turn
        
        claude_response = ""
        async for message in query(prompt=analysis_prompt, options=options):
            # Extract the response content
            if hasattr(message, "content"):
                content = str(message.content)
                # Handle list of TextBlocks
                if "[TextBlock(" in content:
                    import re
                    text_matches = re.findall(r'TextBlock\(text="([^"]*)"', content)
                    if text_matches:
                        claude_response = " ".join(text_matches)
                else:
                    claude_response = content
                break
        
        if claude_response:
            # Parse Claude's comprehensive response
            response_lower = claude_response.lower()
            
            # Extract success assessment
            actual_success = None
            if any(phrase in response_lower for phrase in [
                "did not actually succeed", "task failed", "not successful", "unsuccessful"
            ]):
                actual_success = False
            elif any(phrase in response_lower for phrase in [
                "task succeeded", "completed successfully", "successful", "accomplished"
            ]):
                actual_success = True
                
            # Check for discrepancy mentions
            discrepancy = any(phrase in response_lower for phrase in [
                "discrepancy", "false positive", "claimed success", "incorrectly reported"
            ])
            
            # Extract failure reasons and issues
            failure_reasons = []
            if "permission denied" in response_lower:
                failure_reasons.append("Permission denied")
            if "authentication" in response_lower and ("failed" in response_lower or "required" in response_lower):
                failure_reasons.append("Authentication required")
            if "not authenticated" in response_lower:
                failure_reasons.append("Not authenticated")
            if "access denied" in response_lower:
                failure_reasons.append("Access denied")
                
            # Extract help usage insights
            help_used = any(phrase in response_lower for phrase in [
                "used help", "help flag", "--help", "-h"
            ])
            
            # Extract recommendations (look for recommendation sections)
            recommendations = []
            if "recommend" in response_lower:
                # This is basic - Claude's full response will be in observations
                recommendations.append("See detailed Claude analysis for specific recommendations")
                
            return {
                "actual_success": actual_success,
                "discrepancy": discrepancy,
                "failure_reasons": failure_reasons,
                "help_used": help_used,
                "recommendations": recommendations,
                "evidence_summary": claude_response[:300] + "..." if len(claude_response) > 300 else claude_response,
                "claude_analysis": claude_response
            }
        else:
            # No response received
            raise Exception("No response from Claude Code SDK")
            
    except Exception as e:
        # Fallback to basic pattern detection
        trace_text = " ".join(trace_summary).lower()
        
        actual_success = None
        failure_reasons = []
        
        if "claude requested permissions" in trace_text or "haven't granted" in trace_text:
            actual_success = False
            failure_reasons.append("Permission denied - agent couldn't perform required actions")
        
        # Check for agent claiming failure
        if "failure" in trace_text or "cannot complete" in trace_text:
            actual_success = False
            failure_reasons.append("Agent reported failure")
        
        # Calculate discrepancy
        discrepancy = False
        if actual_success is not None and claimed_success is not None:
            discrepancy = actual_success != claimed_success
        
        return {
            "actual_success": actual_success,
            "discrepancy": discrepancy,
            "failure_reasons": failure_reasons,
            "evidence_summary": f"Fallback analysis - Claude Code SDK error: {str(e)}",
            "fallback_used": True
        }
