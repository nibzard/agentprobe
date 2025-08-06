"""Claude Code SDK integration for running test scenarios."""

import os
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from claude_code_sdk import query, ClaudeCodeOptions, ResultMessage
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live

from .config import load_oauth_token
from .scenario_parser import parse_scenario, get_scenario_options


def _clean_version_string(tool: str, version_line: str) -> str:
    """Clean up version output to extract just the version number.
    
    Args:
        tool: The tool name (e.g., 'git', 'vercel')
        version_line: Raw version output line
        
    Returns:
        Cleaned version string
    """
    import re
    
    # Common patterns to clean up
    # For "git version 2.39.5 (Apple Git-154)" -> "2.39.5"
    if tool == "git" and "git version " in version_line:
        match = re.search(r'git version (\d+\.\d+\.\d+)', version_line)
        if match:
            return match.group(1)
    
    # For "vercel 28.4.8" -> "28.4.8"
    if tool == "vercel":
        match = re.search(r'vercel (\d+\.\d+\.\d+)', version_line)
        if match:
            return match.group(1)
    
    # For "gh version 2.32.1 (2023-07-18)" -> "2.32.1"
    if tool == "gh":
        match = re.search(r'gh version (\d+\.\d+\.\d+)', version_line)
        if match:
            return match.group(1)
    
    # For "Docker version 24.0.5, build ced0996" -> "24.0.5"
    if tool == "docker":
        match = re.search(r'Docker version (\d+\.\d+\.\d+)', version_line)
        if match:
            return match.group(1)
    
    # Generic pattern: extract first semantic version found
    version_match = re.search(r'(\d+\.\d+\.\d+(?:\.\d+)?)', version_line)
    if version_match:
        return version_match.group(1)
    
    # If no specific pattern matches, return the original line
    return version_line


def detect_tool_version(tool: str) -> Dict[str, Any]:
    """Detect the version of a CLI tool by trying common version commands.
    
    Args:
        tool: The name of the CLI tool (e.g., 'vercel', 'gh', 'docker')
        
    Returns:
        Dict containing version info:
        {
            'version': str,  # Version string or 'unknown' if detection failed
            'command_used': str,  # Command that worked, or None if failed
            'raw_output': str,  # Raw command output
            'detection_success': bool  # Whether detection succeeded
        }
    """
    # Common version command patterns to try
    version_commands = [
        f"{tool} --version",
        f"{tool} -v",
        f"{tool} version"
    ]
    
    for cmd in version_commands:
        try:
            # Run command with timeout and capture output
            result = subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                timeout=10,  # 10 second timeout
                check=False  # Don't raise exception on non-zero exit
            )
            
            # If command succeeded and has output, consider it successful
            if result.returncode == 0 and result.stdout.strip():
                raw_output = result.stdout.strip()
                # Extract version from output (take first line, clean it up)
                version_line = raw_output.split('\n')[0].strip()
                
                # Clean up common version output patterns
                cleaned_version = _clean_version_string(tool, version_line)
                
                return {
                    'version': cleaned_version,
                    'command_used': cmd,
                    'raw_output': raw_output,
                    'detection_success': True
                }
            
            # If stdout is empty but stderr has output, check stderr
            elif result.returncode == 0 and result.stderr.strip():
                raw_output = result.stderr.strip()
                version_line = raw_output.split('\n')[0].strip()
                
                # Clean up common version output patterns
                cleaned_version = _clean_version_string(tool, version_line)
                
                return {
                    'version': cleaned_version,
                    'command_used': cmd,
                    'raw_output': raw_output,
                    'detection_success': True
                }
                
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            # Command failed, try next one
            continue
    
    # All commands failed
    return {
        'version': 'unknown',
        'command_used': None,
        'raw_output': '',
        'detection_success': False
    }


async def run_test(
    tool: str,
    scenario_name: str,
    work_dir: Optional[Path] = None,
    oauth_token_file: Optional[Path] = None,
    show_progress: bool = True
) -> Dict[str, Any]:
    """Run a test scenario using Claude Code SDK."""
    # Load scenario prompt
    scenario_path = (
        Path(__file__).parent
        / "scenarios"
        / tool
        / f"{scenario_name}.txt"
    )

    if not scenario_path.exists():
        raise FileNotFoundError(f"Scenario not found: {scenario_path}")

    # Parse scenario with frontmatter support
    scenario_data = parse_scenario(scenario_path)
    prompt = scenario_data['content']
    metadata = scenario_data['metadata']
    
    # Get options from metadata
    scenario_options = get_scenario_options(metadata)

    # Configure options with defaults and scenario overrides
    options_dict = {
        'max_turns': 50,
        'cwd': str(work_dir) if work_dir else None,
        'model': 'sonnet',
        'allowed_tools': ["Read", "Write", "Bash"],
        'permission_mode': "acceptEdits"
    }
    
    # Apply scenario-specific overrides
    options_dict.update(scenario_options)
    
    # Create options object
    options = ClaudeCodeOptions(**options_dict)

    # Load OAuth token and create isolated environment
    oauth_token = load_oauth_token(oauth_token_file)

    # Detect tool version before execution
    version_info = detect_tool_version(tool)

    # Execute scenario with isolated environment
    trace = []
    console = Console()
    start_time = time.time()
    turn_count = 0
    
    # Create progress indicator
    spinner = Spinner("dots", text="[cyan]Agent starting...[/cyan]")
    
    async def execute_with_progress():
        nonlocal turn_count
        if oauth_token:
            # Save original environment
            original_oauth_env = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
            original_api_key = os.environ.get("ANTHROPIC_API_KEY")

            # CRITICAL: Remove API key to force OAuth usage
            if original_api_key:
                del os.environ["ANTHROPIC_API_KEY"]

            # Set token for this execution
            os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = oauth_token

            try:
                async for message in query(prompt=prompt, options=options):
                    trace.append(message)
                    # Update progress for assistant messages
                    if show_progress:
                        message_type = getattr(message, "type", None)
                        message_class = type(message).__name__
                        if (message_type == "assistant" or 
                            message_class in ["AssistantMessage", "TextMessage"] or
                            (hasattr(message, "role") and getattr(message, "role") == "assistant")):
                            turn_count += 1
                            elapsed = int(time.time() - start_time)
                            spinner.update(text=f"[cyan]Agent running... (Turn {turn_count}, {elapsed}s)[/cyan]")
            finally:
                # Restore original environment
                if original_oauth_env is not None:
                    os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = original_oauth_env
                else:
                    os.environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)

                if original_api_key:
                    os.environ["ANTHROPIC_API_KEY"] = original_api_key
        else:
            # No token configured, use normal execution
            async for message in query(prompt=prompt, options=options):
                trace.append(message)
                # Update progress for assistant messages
                if show_progress:
                    message_type = getattr(message, "type", None)
                    message_class = type(message).__name__
                    if (message_type == "assistant" or 
                        message_class in ["AssistantMessage", "TextMessage"] or
                        (hasattr(message, "role") and getattr(message, "role") == "assistant")):
                        turn_count += 1
                        elapsed = int(time.time() - start_time)
                        spinner.update(text=f"[cyan]Agent running... (Turn {turn_count}, {elapsed}s)[/cyan]")
    
    # Run with live progress display if enabled
    if show_progress:
        with Live(spinner, console=console, refresh_per_second=4):
            await execute_with_progress()
    else:
        await execute_with_progress()

    # Extract result
    result = {
        "tool": tool,
        "scenario": scenario_name,
        "scenario_text": prompt,  # Include the actual scenario text
        "scenario_metadata": metadata,  # Include parsed metadata
        "trace": trace,
        "success": False,
        "duration_seconds": 0,
        "cost_usd": 0,
        "tool_version": version_info["version"],
        "version_detection_method": version_info["command_used"],
        "version_detection_success": version_info["detection_success"],
    }

    # Process final result message
    if trace and isinstance(trace[-1], ResultMessage):
        final = trace[-1]
        result["success"] = getattr(final, "subtype", None) == "success"
        result["duration_seconds"] = getattr(final, "duration_ms", 0) / 1000
        result["cost_usd"] = getattr(final, "total_cost_usd", 0)

    return result
