"""Generic analysis of CLI execution traces."""

from typing import List, Dict, Any, Optional
from pathlib import Path
from claude_code_sdk import ResultMessage
import json
import tempfile
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from .config import load_oauth_token


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
    tool_name: str = "",
    oauth_token_file: Optional[Path] = None
) -> Dict[str, Any]:
    """Enhanced analysis combining traditional patterns with LLM insights."""
    
    # Start with traditional analysis
    traditional_analysis = analyze_trace(trace)
    
    # Add Claude CLI analysis if scenario info is available
    if scenario_text and tool_name:
        try:
            claude_analysis = await claude_analyze_trace(
                trace, scenario_text, tool_name, 
                claimed_success=traditional_analysis["success"],
                oauth_token_file=oauth_token_file
            )
            
            # Merge analyses
            enhanced_analysis = traditional_analysis.copy()
            
            # Override success if Claude detected discrepancy
            if claude_analysis.get("discrepancy"):
                enhanced_analysis["success"] = claude_analysis.get("actual_success", False)
                enhanced_analysis["observations"].append(
                    "⚠️ Claude detected discrepancy between claimed and actual success"
                )
            
            # Add AX-specific insights
            if claude_analysis.get("ax_score"):
                enhanced_analysis["ax_score"] = claude_analysis["ax_score"]
            
            if claude_analysis.get("ax_summary"):
                enhanced_analysis["ax_summary"] = claude_analysis["ax_summary"]
            
            # Use Claude's insights to populate all fields - no hardcoded patterns
            if claude_analysis.get("cli_friction_points"):
                enhanced_analysis["observations"].extend(claude_analysis["cli_friction_points"])
            elif claude_analysis.get("failure_reasons"):
                enhanced_analysis["observations"].extend(claude_analysis["failure_reasons"])
            
            # Add Claude's recommendations directly
            if claude_analysis.get("ax_improvements"):
                enhanced_analysis["recommendations"].extend(claude_analysis["ax_improvements"])
            elif claude_analysis.get("recommendations"):
                enhanced_analysis["recommendations"].extend(claude_analysis["recommendations"])
            
            # Store help usage for reporting without hardcoded messages
            enhanced_analysis["help_used"] = claude_analysis.get("help_used", False)
            enhanced_analysis["help_useful"] = claude_analysis.get("help_useful", False)
            
            # Store Claude's analysis for detailed reporting
            enhanced_analysis["claude_analysis"] = claude_analysis.get("claude_analysis", "")
            
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


def load_analysis_prompt(
    scenario_text: str,
    tool_name: str, 
    trace_text: str,
    claimed_success: bool = None
) -> tuple[str, str]:
    """Load and render the analysis prompt template with versioning.
    
    Returns:
        tuple: (rendered_prompt, prompt_version)
    """
    # Get the project root directory
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent  # src/agentprobe/analyzer.py -> project_root
    prompts_dir = project_root / "prompts"
    
    # Load version information from metadata
    metadata_file = prompts_dir / "metadata.json"
    prompt_version = "1.0.0"  # fallback version
    
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                prompt_version = metadata.get("analysis.jinja2", {}).get("version", "1.0.0")
        except (json.JSONDecodeError, IOError):
            # Use fallback version if metadata can't be read
            pass
    
    # Set up Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(prompts_dir),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    # Load the template
    template = env.get_template("analysis.jinja2")
    
    # Prepare template variables
    template_vars = {
        "version": prompt_version,
        "timestamp": datetime.now().isoformat(),
        "scenario_text": scenario_text,
        "tool_name": tool_name,
        "trace_text": trace_text,
        "claimed_success": claimed_success,
        "none": None  # For Jinja2 comparison
    }
    
    # Render the prompt
    rendered_prompt = template.render(**template_vars)
    
    return rendered_prompt, prompt_version


def run_claude_analysis_subprocess(
    trace_summary: List[str], 
    scenario_text: str, 
    tool_name: str,
    claimed_success: bool = None,
    oauth_token_file: Optional[Path] = None
) -> Dict[str, Any]:
    """Run Claude analysis in a separate process to completely avoid async context issues."""
    
    # Create analysis prompt using template
    trace_text = "\n".join(trace_summary)
    analysis_prompt, prompt_version = load_analysis_prompt(
        scenario_text, tool_name, trace_text, claimed_success
    )

    # Write prompt to temporary file for subprocess
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(analysis_prompt)
            prompt_file = f.name
        
        # Use subprocess to run Claude CLI analysis
        import subprocess
        import sys
        
        # Create analysis script without f-string conflicts
        analysis_script = '''
import asyncio
import json
import sys
from claude_code_sdk import query, ClaudeCodeOptions

async def main():
    try:
        with open('{prompt_file}', 'r') as f:
            prompt = f.read()
        
        options = ClaudeCodeOptions(
            max_turns=3,
            cwd=None,
        )
        
        # Debug logging
        print("DEBUG: Starting Claude analysis", file=sys.stderr)
        
        analysis_trace = []
        async for message in query(prompt=prompt, options=options):
            analysis_trace.append(message)
        
        print(f"DEBUG: Received {{len(analysis_trace)}} messages", file=sys.stderr)
        
        # Extract JSON response from Claude's messages
        for message in reversed(analysis_trace):
            if hasattr(message, "content") and message.content:
                # Extract text from TextBlock objects
                content = ""
                if isinstance(message.content, list):
                    text_parts = []
                    for block in message.content:
                        if hasattr(block, 'text'):
                            text_parts.append(block.text)
                        else:
                            text_parts.append(str(block))
                    content = ' '.join(text_parts)
                else:
                    content = str(message.content)
                
                print(f"DEBUG: Extracted content length: {{len(content)}}", file=sys.stderr)
                
                # Look for JSON code blocks first
                if '```json' in content:
                    print("DEBUG: Found JSON code block", file=sys.stderr)
                    start = content.find('```json') + 7
                    end = content.find('```', start)
                    if end > start:
                        json_str = content[start:end].strip()
                        print(f"DEBUG: JSON string length: {{len(json_str)}}", file=sys.stderr)
                        try:
                            result = json.loads(json_str)
                            # Store full Claude response separately to avoid JSON serialization issues
                            result["claude_analysis"] = content[:1000] + "..." if len(content) > 1000 else content
                            # Map new fields to old field names for compatibility
                            if "cli_friction_points" in result and "failure_reasons" not in result:
                                result["failure_reasons"] = result["cli_friction_points"]
                            if "ax_improvements" in result and "recommendations" not in result:
                                result["recommendations"] = result["ax_improvements"]
                            print(json.dumps(result))
                            return
                        except json.JSONDecodeError as e:
                            print(f"DEBUG: JSON decode error: {{e}}", file=sys.stderr)
                
                # Look for direct JSON - find the first {{ and last }}
                first_brace = content.find('{{')
                last_brace = content.rfind('}}')
                if first_brace >= 0 and last_brace > first_brace:
                    json_str = content[first_brace:last_brace+1]
                    try:
                        result = json.loads(json_str)
                        result["claude_analysis"] = content[:1000] + "..." if len(content) > 1000 else content
                        # Map new fields to old field names for compatibility
                        if "cli_friction_points" in result and "failure_reasons" not in result:
                            result["failure_reasons"] = result["cli_friction_points"]
                        if "ax_improvements" in result and "recommendations" not in result:
                            result["recommendations"] = result["ax_improvements"]
                        print(json.dumps(result))
                        return
                    except json.JSONDecodeError as e:
                        print(f"DEBUG: Direct JSON decode error: {{e}}", file=sys.stderr)
        
        # Fallback if no JSON found
        print("DEBUG: No valid JSON found, using fallback", file=sys.stderr)
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
        print(f"DEBUG: Exception occurred: {{type(e).__name__}}: {{str(e)}}", file=sys.stderr)
        error_result = {{
            "actual_success": None,
            "discrepancy": False,
            "failure_reasons": ["Analysis failed: " + str(e)],
            "help_used": False,
            "recommendations": ["Manual review needed"],
            "claude_analysis": "Error: " + str(e)
        }}
        print(json.dumps(error_result))

if __name__ == "__main__":
    asyncio.run(main())
'''.format(prompt_file=prompt_file)
        
        # Write the script to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(analysis_script)
            script_file = f.name
        
        # Load OAuth token and create isolated environment for subprocess
        oauth_token = load_oauth_token(oauth_token_file)
        env = os.environ.copy()
        
        if oauth_token:
            env["CLAUDE_CODE_OAUTH_TOKEN"] = oauth_token
            # CRITICAL: Remove API key from subprocess to force OAuth usage
            if env.get("ANTHROPIC_API_KEY"):
                del env["ANTHROPIC_API_KEY"]
        
        # Run the analysis script in subprocess
        result = subprocess.run(
            [sys.executable, script_file],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            env=env
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
        # Also print stderr for debugging
        if result.stderr:
            print(f"Subprocess stderr:\n{result.stderr}", file=sys.stderr)
        
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
        except OSError:
            pass


async def claude_analyze_trace(
    trace: List[Dict[str, Any]], 
    scenario_text: str, 
    tool_name: str,
    claimed_success: bool = None,
    oauth_token_file: Optional[Path] = None
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
            claimed_success,
            oauth_token_file
        )
        
        # Add prompt version to the result for tracking
        if claude_result and not claude_result.get("subprocess_error"):
            _, prompt_version = load_analysis_prompt("", "", "", None)
            claude_result["prompt_version"] = prompt_version
        
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
