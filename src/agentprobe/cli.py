"""AgentProbe CLI - Test how well AI agents interact with CLI tools."""

import typer
import asyncio
from pathlib import Path
from typing import Optional

from .runner import run_test
from .analyzer import aggregate_analyses, enhanced_analyze_trace
from .reporter import print_report, print_aggregate_report

app = typer.Typer(
    name="agentprobe",
    help="Test how well AI agents interact with CLI tools",
    add_completion=False,
)


def print_trace_details(trace, run_label: str = ""):
    """Print detailed trace information for debugging."""
    label = f" {run_label}" if run_label else ""
    typer.echo(f"\n--- Full Trace{label} ---")
    
    if not trace:
        typer.echo("No trace messages found")
        return
    
    # Show summary first
    message_types = {}
    for message in trace:
        message_type = getattr(message, "type", "unknown")
        message_class = type(message).__name__
        key = f"{message_class} (type={message_type})"
        message_types[key] = message_types.get(key, 0) + 1
    
    typer.echo(f"Trace Summary: {len(trace)} messages")
    for msg_type, count in message_types.items():
        typer.echo(f"  {count}x {msg_type}")
    typer.echo("")
    
    # Show detailed messages
    for i, message in enumerate(trace):
        message_type = getattr(message, "type", "unknown")
        message_class = type(message).__name__
        typer.echo(f"{i+1}: [{message_class}] type={message_type}")
        
        # Show attributes for debugging
        if hasattr(message, "__dict__"):
            for attr, value in message.__dict__.items():
                if attr not in ["type"]:  # Skip type since we already show it
                    typer.echo(f"    {attr}: {str(value)[:100]}")
        else:
            typer.echo(f"    Raw: {str(message)[:200]}")
        typer.echo("")  # Add spacing between messages


@app.command()
def test(
    tool: str = typer.Argument(..., help="CLI tool to test (e.g., vercel, gh, docker)"),
    scenario: str = typer.Option(..., "--scenario", "-s", help="Scenario name to run"),
    work_dir: Optional[Path] = typer.Option(
        None, "--work-dir", "-w", help="Working directory"
    ),
    max_turns: int = typer.Option(20, "--max-turns", help="Maximum agent interactions"),
    runs: int = typer.Option(1, "--runs", help="Number of times to run the scenario"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed trace"),
):
    """Run a test scenario against a CLI tool."""

    async def _run():
        try:
            if runs == 1:
                # Single run - use enhanced analysis
                result = await run_test(tool, scenario, work_dir)
                analysis = await enhanced_analyze_trace(
                    result["trace"], 
                    result.get("scenario_text", ""), 
                    result["tool"]
                )
                print_report(result, analysis)

                if verbose:
                    print_trace_details(result["trace"])
            else:
                # Multiple runs - collect all results
                results = []
                analyses = []
                
                for run_num in range(1, runs + 1):
                    typer.echo(f"Running {tool}/{scenario} - Run {run_num}/{runs}")
                    
                    result = await run_test(tool, scenario, work_dir)
                    analysis = await enhanced_analyze_trace(
                        result["trace"], 
                        result.get("scenario_text", ""), 
                        result["tool"]
                    )
                    
                    results.append(result)
                    analyses.append(analysis)
                    
                    if verbose:
                        typer.echo(f"\n--- Run {run_num} Individual Result ---")
                        print_report(result, analysis)
                        print_trace_details(result["trace"], f"for Run {run_num}")
                
                # Print aggregate report
                aggregate_analysis = aggregate_analyses(analyses)
                print_aggregate_report(results, aggregate_analysis, verbose)

        except FileNotFoundError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"Unexpected error: {e}", err=True)
            raise typer.Exit(1)

    asyncio.run(_run())


@app.command()
def benchmark(
    tool: Optional[str] = typer.Argument(None, help="Tool to benchmark"),
    all: bool = typer.Option(False, "--all", help="Run all benchmarks"),
):
    """Run benchmark tests for CLI tools."""

    async def _run():
        scenarios_dir = Path(__file__).parent / "scenarios"

        tools_to_test = []
        if all:
            tools_to_test = [d.name for d in scenarios_dir.iterdir() if d.is_dir()]
        elif tool:
            tools_to_test = [tool]
        else:
            typer.echo("Error: Specify a tool or use --all flag", err=True)
            raise typer.Exit(1)

        for tool_name in tools_to_test:
            tool_dir = scenarios_dir / tool_name
            if not tool_dir.exists():
                typer.echo(f"Warning: No scenarios found for {tool_name}")
                continue

            typer.echo(f"\n=== Benchmarking {tool_name.upper()} ===")

            for scenario_file in tool_dir.glob("*.txt"):
                scenario_name = scenario_file.stem
                try:
                    result = await run_test(tool_name, scenario_name)
                    analysis = await enhanced_analyze_trace(
                        result["trace"], 
                        result.get("scenario_text", ""), 
                        result["tool"]
                    )
                    print_report(result, analysis)
                except Exception as e:
                    typer.echo(f"Failed {tool_name}/{scenario_name}: {e}", err=True)

    asyncio.run(_run())


@app.command()
def report(
    format: str = typer.Option(
        "text", "--format", "-f", help="Output format (text/json/markdown)"
    ),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Generate reports from test results."""
    typer.echo("Note: Report generation from stored results not yet implemented.")
    typer.echo("Use 'agentprobe benchmark --all' to run tests and see results.")
    typer.echo(
        f"Future: Will support {format} format" + (f" to {output}" if output else "")
    )


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
