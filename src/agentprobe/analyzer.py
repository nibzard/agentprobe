"""Generic analysis of CLI execution traces."""

from typing import List, Dict, Any
from claude_code_sdk import ResultMessage, query, ClaudeCodeOptions
import concurrent.futures
import anyio
import asyncio
import json
import tempfile
import os


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
            
            # Note analysis method used
            if claude_analysis.get("subprocess_error"):
                enhanced_analysis["observations"].append(
                    f"⚠️ Subprocess-based Claude analysis failed: {claude_analysis.get('subprocess_error')}"
                )
            elif claude_analysis.get("fallback_used"):
                enhanced_analysis["observations"].append(
                    "⚠️ Using minimal fallback analysis (Claude analysis failed)"
                )
            else:
                enhanced_analysis["observations"].append(
                    "✅ Using Claude Code SDK analysis (subprocess-based)"
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


def run_claude_analysis_subprocess(
    trace_summary: List[str], 
    scenario_text: str, 
    tool_name: str,
    claimed_success: bool = None
) -> Dict[str, Any]:
    """Run Claude analysis in a separate process to completely avoid async context issues."""
    
    # Create analysis prompt
    trace_text = "\n".join(trace_summary)
    
    analysis_prompt = f"""
I need you to analyze the execution trace of an AI agent trying to complete a CLI task and determine if it actually succeeded or failed.

**Original Task/Scenario:**
{scenario_text}

**CLI Tool:** {tool_name}

**Agent's Claimed Result:** {"SUCCESS" if claimed_success else "FAILURE" if claimed_success is not None else "UNKNOWN"}

**Full Execution Trace:**
{trace_text}

Please analyze this trace and provide:

1. **Actual Success**: Did the agent actually complete the task successfully? (true/false)
2. **Discrepancy**: Is there a difference between what the agent claimed and what actually happened?
3. **Failure Reasons**: If it failed, what were the specific reasons?
4. **Help Usage**: Did the agent appropriately use help flags or documentation?
5. **Recommendations**: What could be improved for better CLI usability?

Focus on:
- Permission denials and authentication issues
- Actual file/resource creation vs. claims
- CLI syntax errors and unknown options
- Whether the final state matches the intended goal
- Any false positive success claims

Respond in JSON format:
{{
    "actual_success": boolean,
    "discrepancy": boolean,
    "failure_reasons": ["reason1", "reason2"],
    "help_used": boolean,
    "recommendations": ["rec1", "rec2"],
    "claude_analysis": "detailed explanation of your analysis"
}}
"""

    # Write prompt to temporary file for subprocess
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(analysis_prompt)
            prompt_file = f.name
        
        # Use subprocess to run Claude CLI analysis
        import subprocess
        import sys
        
        # Create analysis script using proper string formatting
        analysis_script_template = '''
import asyncio
import json
import sys
import re
from claude_code_sdk import query, ClaudeCodeOptions

async def main():
    try:
        with open('{prompt_file}', 'r') as f:
            prompt = f.read()
        
        options = ClaudeCodeOptions(
            max_turns=3,
            cwd=None,
        )
        
        analysis_trace = []
        async for message in query(prompt=prompt, options=options):
            analysis_trace.append(message)
        
        # Extract JSON response - look for JSON blocks
        for message in reversed(analysis_trace):
            if hasattr(message, "content") and message.content:
                content = str(message.content)
                
                # Look for JSON code blocks first
                if '```json' in content:
                    start = content.find('```json') + 7
                    end = content.find('```', start)
                    if end > start:
                        json_str = content[start:end].strip()
                        try:
                            result = json.loads(json_str)
                            result["claude_analysis"] = content
                            print(json.dumps(result))
                            return
                        except json.JSONDecodeError:
                            pass
                
                # Look for direct JSON - balanced brace approach
                brace_count = 0
                start_idx = -1
                for i, char in enumerate(content):
                    if char == '{{':
                        if start_idx == -1:
                            start_idx = i
                        brace_count += 1
                    elif char == '}}':
                        brace_count -= 1
                        if brace_count == 0 and start_idx != -1:
                            json_str = content[start_idx:i+1]
                            try:
                                result = json.loads(json_str)
                                result["claude_analysis"] = content
                                print(json.dumps(result))
                                return
                            except json.JSONDecodeError:
                                pass
                            break
        
        # Fallback if no JSON found
        fallback_result = {{
            "actual_success": None,
            "discrepancy": False,
            "failure_reasons": ["Could not parse Claude response"],
            "help_used": False,
            "recommendations": ["Manual review needed"],
            "claude_analysis": "Analysis parsing failed"
        }}
        print(json.dumps(fallback_result))
        
    except Exception as e:
        error_result = {{
            "actual_success": None,
            "discrepancy": False,
            "failure_reasons": [f"Analysis failed: {{str(e)}}"],
            "help_used": False,
            "recommendations": ["Manual review needed"],
            "claude_analysis": f"Error: {{str(e)}}"
        }}
        print(json.dumps(error_result))

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        analysis_script = analysis_script_template.format(prompt_file=prompt_file)
        
        # Write the script to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(analysis_script)
            script_file = f.name
        
        # Run the analysis script in subprocess
        result = subprocess.run(
            [sys.executable, script_file],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            env=os.environ.copy()  # Pass environment variables
        )
        
        # Parse the JSON output
        if result.returncode == 0 and result.stdout.strip():
            try:
                return json.loads(result.stdout.strip())
            except json.JSONDecodeError as e:
                # Try to extract just the JSON part from stdout
                stdout = result.stdout.strip()
                # Look for JSON in the output
                if '```json' in stdout:
                    start = stdout.find('```json') + 7
                    end = stdout.find('```', start)
                    if end > start:
                        json_str = stdout[start:end].strip()
                        try:
                            parsed_result = json.loads(json_str)
                            return parsed_result
                        except json.JSONDecodeError:
                            pass
                
                # Add debug info about parsing failure
                return {
                    "actual_success": None,
                    "discrepancy": False,
                    "failure_reasons": [f"JSON parse error: {str(e)[:100]}"],
                    "help_used": False,
                    "recommendations": ["Manual review needed"],
                    "claude_analysis": f"Parse error. Stdout: {result.stdout[:500]}",
                    "subprocess_error": True
                }
        
        # If subprocess failed, return error info
        return {
            "actual_success": None,
            "discrepancy": False,
            "failure_reasons": [f"Subprocess analysis failed (code {result.returncode}): {result.stderr[:200]}"],
            "help_used": False,
            "recommendations": ["Manual review needed"],
            "claude_analysis": f"Subprocess error: {result.stderr[:200]} | Stdout: {result.stdout[:200]}",
            "subprocess_error": True
        }
        
    except Exception as e:
        return {
            "actual_success": None,
            "discrepancy": False,
            "failure_reasons": [f"Process-based analysis failed: {str(e)}"],
            "help_used": False,
            "recommendations": ["Consider running analysis separately"],
            "claude_analysis": f"Analysis failed due to: {str(e)}",
            "subprocess_error": True
        }
    finally:
        # Clean up temp files
        try:
            if 'prompt_file' in locals():
                os.unlink(prompt_file)
            if 'script_file' in locals():
                os.unlink(script_file)
        except:
            pass


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
            content = str(message.content)[:500]  # Increased limit for better analysis
        elif hasattr(message, "result"):
            content = str(getattr(message, "result", ""))[:500]
        else:
            content = str(message)[:500]
            
        trace_summary.append(f"{i}. [{message_class}] {content}")
    
    try:
        # Use subprocess-based execution to completely avoid async context issues
        claude_result = run_claude_analysis_subprocess(
            trace_summary,
            scenario_text,
            tool_name,
            claimed_success
        )
        
        # Return the Claude analysis result
        return claude_result
            
    except Exception as e:
        # Minimal fallback - just basic pattern detection
        trace_text = " ".join(trace_summary).lower()
        
        # Only detect the most obvious failure patterns
        failure_reasons = []
        if "claude requested permissions" in trace_text or "haven't granted" in trace_text:
            failure_reasons.append("Permission denied")
        if "unknown or unexpected option" in trace_text:
            failure_reasons.append("CLI syntax error")
        
        return {
            "actual_success": None,
            "discrepancy": False,
            "failure_reasons": failure_reasons,
            "help_used": "--help" in trace_text or "-h" in trace_text,
            "recommendations": ["Claude analysis failed - manual review needed"],
            "claude_analysis": f"Analysis failed: {str(e)}",
            "fallback_used": True,
            "subprocess_error": str(e)
        }
