"""Output formatting for AgentProbe results."""

from rich.console import Console
from rich.panel import Panel
from typing import Dict, Any


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
