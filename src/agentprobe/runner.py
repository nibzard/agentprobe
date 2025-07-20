"""Claude Code SDK integration for running test scenarios."""

from pathlib import Path
from typing import Dict, Any
from claude_code_sdk import query, ClaudeCodeOptions, ResultMessage


async def run_test(
    tool: str, scenario_name: str, work_dir: Path = None
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
    )

    # Execute scenario
    trace = []
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
