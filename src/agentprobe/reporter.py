"""Output formatting for AgentProbe results."""

from rich.console import Console
from rich.panel import Panel
from typing import Dict, Any, List


def print_report(result: Dict[str, Any], analysis: Dict[str, Any]) -> None:
    """Print formatted report to terminal."""
    console = Console()

    # Create status emoji
    status = "✓ SUCCESS" if result["success"] else "❌ FAILED"

    # Build summary
    summary_lines = []
    if result["success"]:
        summary_lines.append("• Task completed successfully")
    else:
        summary_lines.append("• Task failed to complete")

    summary_lines.append(f"• Required {analysis['total_turns']} turns to complete")

    if analysis["errors_encountered"]:
        summary_lines.append(
            f"• Encountered {len(analysis['errors_encountered'])} errors"
        )

    # Build content
    content = f"""[bold]Tool:[/bold] {result['tool']} | [bold]Scenario:[/bold] {result['scenario']}
[bold]Status:[/bold] {status} | [bold]Duration:[/bold] {result['duration_seconds']:.1f}s | [bold]Cost:[/bold] ${result['cost_usd']:.3f}

[bold]Summary:[/bold]
{chr(10).join(summary_lines)}"""

    # Add observations if any
    if analysis["observations"]:
        content += "\n\n[bold]Observations:[/bold]\n"
        for obs in analysis["observations"]:
            content += f"• {obs}\n"

    # Add recommendations if any
    if analysis["recommendations"]:
        content += "\n[bold]Recommendations:[/bold]\n"
        for rec in analysis["recommendations"]:
            content += f"• {rec}\n"

    # Print panel
    console.print(
        Panel(content.strip(), title="AgentProbe Results", border_style="blue")
    )


def print_aggregate_report(
    results: List[Dict[str, Any]], 
    aggregate_analysis: Dict[str, Any], 
    verbose: bool = False
) -> None:
    """Print formatted aggregate report for multiple runs."""
    console = Console()
    
    if not results or not aggregate_analysis:
        console.print("[red]No results to aggregate[/red]")
        return
    
    # Calculate aggregate metrics
    total_runs = aggregate_analysis["total_runs"]
    success_rate = aggregate_analysis["success_rate"]
    
    # Calculate cost and duration statistics
    durations = [result["duration_seconds"] for result in results]
    costs = [result["cost_usd"] for result in results]
    
    avg_duration = sum(durations) / len(durations)
    total_cost = sum(costs)
    avg_cost = total_cost / len(costs)
    
    # Create status with success rate
    if success_rate == 1.0:
        status = f"✓ SUCCESS ({success_rate:.0%})"
        status_color = "green"
    elif success_rate >= 0.5:
        status = f"⚠ PARTIAL ({success_rate:.0%})"
        status_color = "yellow"
    else:
        status = f"❌ FAILED ({success_rate:.0%})"
        status_color = "red"
    
    # Build summary
    summary_lines = [
        f"• Completed {total_runs} runs with {success_rate:.0%} success rate",
        f"• Average {aggregate_analysis['avg_turns']:.1f} turns (range: {aggregate_analysis['min_turns']}-{aggregate_analysis['max_turns']})",
        f"• Total {aggregate_analysis['total_errors']} errors across all runs",
        f"• Help usage in {aggregate_analysis['help_usage_rate']:.0%} of runs"
    ]
    
    # Build content
    tool = results[0]["tool"]
    scenario = results[0]["scenario"]
    
    content = f"""[bold]Tool:[/bold] {tool} | [bold]Scenario:[/bold] {scenario}
[bold]Status:[/bold] [{status_color}]{status}[/{status_color}] | [bold]Runs:[/bold] {total_runs}
[bold]Duration:[/bold] {avg_duration:.1f}s avg | [bold]Total Cost:[/bold] ${total_cost:.3f} | [bold]Avg Cost:[/bold] ${avg_cost:.3f}

[bold]Summary:[/bold]
{chr(10).join(summary_lines)}"""
    
    # Add common observations if any
    if aggregate_analysis["common_observations"]:
        content += "\n\n[bold]Common Observations:[/bold]\n"
        for obs in aggregate_analysis["common_observations"]:
            content += f"• {obs}\n"
    
    # Add common recommendations if any
    if aggregate_analysis["common_recommendations"]:
        content += "\n[bold]Common Recommendations:[/bold]\n"
        for rec in aggregate_analysis["common_recommendations"]:
            content += f"• {rec}\n"
    
    # Add individual run details if verbose
    if verbose:
        content += "\n[bold]Individual Run Details:[/bold]\n"
        for i, result in enumerate(results, 1):
            run_status = "✓" if result["success"] else "❌"
            trace_count = len(result.get("trace", []))
            content += f"Run {i}: {run_status} {result['duration_seconds']:.1f}s ${result['cost_usd']:.3f} ({trace_count} trace messages)\n"
    
    # Print panel
    console.print(
        Panel(content.strip(), title="AgentProbe Aggregate Results", border_style="blue")
    )
