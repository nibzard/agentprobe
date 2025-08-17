"""AgentProbe - Test how well AI agents interact with CLI tools."""

__version__ = "0.3.12"

from .runner import run_test
from .analyzer import analyze_trace
from .reporter import print_report

__all__ = ["run_test", "analyze_trace", "print_report", "test_cli"]


async def test_cli(tool: str, scenario: str, work_dir=None):
    """High-level API for testing CLI tools."""
    result = await run_test(tool, scenario, work_dir)
    analysis = analyze_trace(result["trace"])
    return {
        "success": result["success"],
        "duration_seconds": result["duration_seconds"],
        "cost_usd": result["cost_usd"],
        "analysis": analysis,
    }
