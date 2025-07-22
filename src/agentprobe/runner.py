"""Claude Code SDK integration for running test scenarios."""

import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from claude_code_sdk import query, ClaudeCodeOptions, ResultMessage
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live

from .config import load_oauth_token
from .scenario_parser import parse_scenario, get_scenario_options


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
    }

    # Process final result message
    if trace and isinstance(trace[-1], ResultMessage):
        final = trace[-1]
        result["success"] = getattr(final, "subtype", None) == "success"
        result["duration_seconds"] = getattr(final, "duration_ms", 0) / 1000
        result["cost_usd"] = getattr(final, "total_cost_usd", 0)

    return result
