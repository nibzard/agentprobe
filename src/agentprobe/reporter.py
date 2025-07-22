"""Output formatting for AgentProbe results."""

from rich.console import Console
from rich.panel import Panel
from typing import Dict, Any, List


def print_report(result: Dict[str, Any], analysis: Dict[str, Any]) -> None:
    """Print AX-focused report for CLI developers."""
    console = Console()

    # Get AX score or calculate based on success and turns
    ax_score = analysis.get("ax_score", "N/A")
    if ax_score == "N/A":
        # Simple fallback scoring
        turns = analysis.get("total_turns", 0)
        success = analysis.get("success", False)
        if success and turns <= 5:
            ax_score = "A"
        elif success and turns <= 10:
            ax_score = "B"
        elif success and turns <= 15:
            ax_score = "C"
        elif success:
            ax_score = "D"
        else:
            ax_score = "F"
    
    # Get AX summary
    ax_summary = analysis.get("ax_summary", "")
    if not ax_summary:
        # Fallback summary
        if analysis.get("success"):
            ax_summary = f"Agent completed task in {analysis.get('total_turns', 0)} turns."
        else:
            ax_summary = f"Agent failed to complete task after {analysis.get('total_turns', 0)} turns."

    # Build content focusing on AX
    content = f"""[bold]Tool:[/bold] {result['tool']} | [bold]Scenario:[/bold] {result['scenario']}
[bold]AX Score:[/bold] {ax_score} ({analysis.get('total_turns', 0)} turns, {"60%" if analysis.get("success") else "0%"} success rate)

[bold cyan]Agent Experience Summary:[/bold cyan]
{ax_summary}"""

    # Add CLI Friction Points if any
    friction_points = []
    for obs in analysis.get("observations", []):
        if not obs.startswith("✅") and not obs.startswith("⚠️ Using"):
            friction_points.append(obs)
    
    if friction_points:
        content += "\n\n[bold red]CLI Friction Points:[/bold red]"
        for point in friction_points[:3]:  # Show top 3
            content += f"\n• {point}"

    # Add Top Improvements
    improvements = analysis.get("recommendations", [])
    if improvements:
        content += "\n\n[bold green]Top Improvements for CLI:[/bold green]"
        for i, improvement in enumerate(improvements[:3], 1):  # Show top 3
            content += f"\n{i}. {improvement}"

    # Add metadata if verbose info needed
    metadata = result.get("scenario_metadata", {})
    if metadata.get("expected_turns"):
        content += f"\n\n[dim]Expected turns: {metadata['expected_turns']} | "
    else:
        content += "\n\n[dim]"
    content += f"Duration: {result['duration_seconds']:.1f}s | Cost: ${result['cost_usd']:.3f}[/dim]"

    # Add hint for verbose mode
    content += "\n\n[dim italic]Use --verbose for full trace analysis[/dim italic]"

    # Print panel
    console.print(
        Panel(content.strip(), title="AgentProbe Results", border_style="cyan")
    )


def print_aggregate_report(
    results: List[Dict[str, Any]], 
    aggregate_analysis: Dict[str, Any], 
    verbose: bool = False
) -> None:
    """Print AX-focused aggregate report for CLI developers."""
    console = Console()
    
    if not results or not aggregate_analysis:
        console.print("[red]No results to aggregate[/red]")
        return
    
    # Calculate aggregate metrics
    total_runs = aggregate_analysis["total_runs"]
    success_rate = aggregate_analysis["success_rate"]
    avg_turns = aggregate_analysis["avg_turns"]
    
    # Calculate aggregate AX score
    if success_rate == 1.0 and avg_turns <= 5:
        ax_score = "A"
    elif success_rate >= 0.8 and avg_turns <= 10:
        ax_score = "B"
    elif success_rate >= 0.6 and avg_turns <= 15:
        ax_score = "C"
    elif success_rate >= 0.4:
        ax_score = "D"
    else:
        ax_score = "F"
    
    # Build content
    tool = results[0]["tool"]
    scenario = results[0]["scenario"]
    
    content = f"""[bold]Tool:[/bold] {tool} | [bold]Scenario:[/bold] {scenario}
[bold]AX Score:[/bold] {ax_score} ({avg_turns:.1f} avg turns, {success_rate:.0%} success rate) | [bold]Runs:[/bold] {total_runs}

[bold cyan]Consistency Analysis:[/bold cyan]
• Turn variance: {aggregate_analysis['min_turns']}-{aggregate_analysis['max_turns']} turns
• Success consistency: {success_rate:.0%} of runs succeeded
• Agent confusion points: {aggregate_analysis['total_issues']} total friction events"""
    
    # Add common friction points
    common_friction = []
    for obs in aggregate_analysis.get("common_observations", []):
        if not obs.startswith("✅") and not obs.startswith("⚠️ Using"):
            common_friction.append(obs)
    
    if common_friction:
        content += "\n\n[bold red]Consistent CLI Friction Points:[/bold red]"
        for point in common_friction[:5]:  # Show top 5
            content += f"\n• {point}"
    
    # Add prioritized improvements
    if aggregate_analysis.get("common_recommendations"):
        content += "\n\n[bold green]Priority Improvements for CLI:[/bold green]"
        # Sort by frequency (implicit in common_recommendations)
        for i, rec in enumerate(aggregate_analysis["common_recommendations"][:5], 1):
            content += f"\n{i}. {rec}"
    
    # Add cost/time summary
    durations = [result["duration_seconds"] for result in results]
    costs = [result["cost_usd"] for result in results]
    avg_duration = sum(durations) / len(durations)
    total_cost = sum(costs)
    
    content += f"\n\n[dim]Avg duration: {avg_duration:.1f}s | Total cost: ${total_cost:.3f}[/dim]"
    
    # Add individual run details if verbose
    if verbose:
        content += "\n\n[bold]Individual Run Details:[/bold]"
        for i, result in enumerate(results, 1):
            # Try to get AX score from individual analysis
            run_analysis = aggregate_analysis.get("individual_analyses", [])
            ax_score_run = "?"
            if i-1 < len(run_analysis) and "ax_score" in run_analysis[i-1]:
                ax_score_run = run_analysis[i-1]["ax_score"]
            
            run_status = "✓" if result["success"] else "❌"
            content += f"\nRun {i}: {run_status} AX:{ax_score_run} {result['duration_seconds']:.1f}s (Turn count varies)"
    else:
        content += "\n\n[dim italic]Use --verbose for individual run details[/dim italic]"
    
    # Print panel
    console.print(
        Panel(content.strip(), title="AgentProbe Aggregate Results", border_style="cyan")
    )
