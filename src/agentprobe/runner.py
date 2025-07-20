"""Claude Code SDK integration for running test scenarios."""

from pathlib import Path
from typing import List, Dict, Any
import asyncio
from claude_code_sdk import query, ClaudeCodeOptions


async def run_test(tool: str, scenario_name: str, work_dir: Path = None) -> Dict[str, Any]:
    """Run a test scenario using Claude Code SDK."""
    # Load scenario prompt
    scenario_path = Path(__file__).parent.parent.parent / "scenarios" / tool / f"{scenario_name}.txt"
    
    if not scenario_path.exists():
        raise FileNotFoundError(f"Scenario not found: {scenario_path}")
    
    prompt = scenario_path.read_text().strip()
    
    # Configure options
    options = ClaudeCodeOptions(
        max_turns=20,
        cwd=str(work_dir) if work_dir else None,
    )
    
    # Execute scenario
    trace = []
    async for message in query(prompt=prompt, options=options):
        trace.append(message)
    
    # Extract result
    result = {
        "tool": tool,
        "scenario": scenario_name,
        "trace": trace,
        "success": False,
        "duration_seconds": 0,
        "cost_usd": 0,
    }
    
    # Process final result message
    if trace and trace[-1].get("type") == "result":
        final = trace[-1]
        result["success"] = final.get("subtype") == "success"
        result["duration_seconds"] = final.get("duration_ms", 0) / 1000
        result["cost_usd"] = final.get("total_cost_usd", 0)
    
    return result