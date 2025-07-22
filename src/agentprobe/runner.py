"""Claude Code SDK integration for running test scenarios."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from claude_code_sdk import query, ClaudeCodeOptions, ResultMessage

from .config import load_oauth_token


async def run_test(
    tool: str, 
    scenario_name: str, 
    work_dir: Optional[Path] = None,
    oauth_token_file: Optional[Path] = None
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

    prompt = scenario_path.read_text().strip()

    # Configure options
    options = ClaudeCodeOptions(
        max_turns=50,
        cwd=str(work_dir) if work_dir else None,
        model="sonnet",
    )

    # Load OAuth token and create isolated environment
    oauth_token = load_oauth_token(oauth_token_file)
    
    # Debug logging
    print(f"[DEBUG] OAuth token loaded: {'Yes' if oauth_token else 'No'}")
    if oauth_token:
        print(f"[DEBUG] OAuth token length: {len(oauth_token)}")
        print(f"[DEBUG] OAuth token prefix: {oauth_token[:15]}...")
    
    # Check existing environment
    existing_oauth = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    existing_api_key = os.environ.get("ANTHROPIC_API_KEY")
    print(f"[DEBUG] Existing CLAUDE_CODE_OAUTH_TOKEN: {'Set' if existing_oauth else 'Not set'}")
    print(f"[DEBUG] Existing ANTHROPIC_API_KEY: {'Set' if existing_api_key else 'Not set'}")
    
    # Execute scenario with isolated environment
    trace = []
    if oauth_token:
        # Save original environment
        original_oauth_env = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
        original_api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        # CRITICAL: Remove API key to force OAuth usage
        if original_api_key:
            print(f"[DEBUG] Temporarily removing ANTHROPIC_API_KEY to force OAuth usage")
            del os.environ["ANTHROPIC_API_KEY"]
        
        # Set token for this execution
        os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = oauth_token
        print(f"[DEBUG] Set CLAUDE_CODE_OAUTH_TOKEN in environment")
        
        # Verify it was set
        print(f"[DEBUG] CLAUDE_CODE_OAUTH_TOKEN after setting: {'Set' if os.environ.get('CLAUDE_CODE_OAUTH_TOKEN') else 'Not set'}")
        print(f"[DEBUG] ANTHROPIC_API_KEY after removal: {'Set' if os.environ.get('ANTHROPIC_API_KEY') else 'Not set'}")
        
        try:
            print(f"[DEBUG] Starting SDK query with OAuth token ONLY")
            async for message in query(prompt=prompt, options=options):
                trace.append(message)
        finally:
            # Restore original environment
            if original_oauth_env is not None:
                os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = original_oauth_env
            else:
                os.environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
            
            if original_api_key:
                os.environ["ANTHROPIC_API_KEY"] = original_api_key
                print(f"[DEBUG] Restored ANTHROPIC_API_KEY")
            
            print(f"[DEBUG] Restored original environment")
    else:
        # No token configured, use normal execution
        print(f"[DEBUG] No OAuth token configured, using SDK defaults")
        async for message in query(prompt=prompt, options=options):
            trace.append(message)

    # Extract result
    result = {
        "tool": tool,
        "scenario": scenario_name,
        "scenario_text": prompt,  # Include the actual scenario text
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
