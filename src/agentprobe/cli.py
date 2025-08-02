"""AgentProbe CLI - Test how well AI agents interact with CLI tools."""

import typer
import asyncio
from pathlib import Path
from typing import Optional

from .runner import run_test
from .analyzer import aggregate_analyses, enhanced_analyze_trace
from .reporter import print_report, print_aggregate_report
from .submission import ResultSubmitter
from .models import TestResult

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
    max_turns: int = typer.Option(50, "--max-turns", help="Maximum agent interactions"),
    runs: int = typer.Option(1, "--runs", help="Number of times to run the scenario"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed trace"),
    oauth_token_file: Optional[Path] = typer.Option(
        None, "--oauth-token-file", help="Path to file containing Claude Code OAuth token"
    ),
    share: bool = typer.Option(False, "--share", help="Share results with the community"),
):
    """Run a test scenario against a CLI tool."""

    async def _run():
        try:
            if runs == 1:
                # Single run - use enhanced analysis
                result = await run_test(tool, scenario, work_dir, oauth_token_file, show_progress=not verbose)
                analysis = await enhanced_analyze_trace(
                    result["trace"],
                    result.get("scenario_text", ""),
                    result["tool"],
                    oauth_token_file
                )
                print_report(result, analysis)

                if verbose:
                    print_trace_details(result["trace"])
                
                # Share result if requested
                if share:
                    submitter = ResultSubmitter()
                    test_result = TestResult(
                        run_id=result.get("run_id", ""),
                        tool=result["tool"],
                        scenario=result["scenario"],
                        trace=result["trace"],
                        duration=result["duration"],
                        analysis=analysis
                    )
                    await submitter.submit_result(test_result, force=True)
            else:
                # Multiple runs - collect all results
                results = []
                analyses = []

                for run_num in range(1, runs + 1):
                    typer.echo(f"Running {tool}/{scenario} - Run {run_num}/{runs}")

                    result = await run_test(tool, scenario, work_dir, oauth_token_file, show_progress=not verbose)
                    analysis = await enhanced_analyze_trace(
                        result["trace"],
                        result.get("scenario_text", ""),
                        result["tool"],
                        oauth_token_file
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
    oauth_token_file: Optional[Path] = typer.Option(
        None, "--oauth-token-file", help="Path to file containing Claude Code OAuth token"
    ),
    share: bool = typer.Option(False, "--share", help="Share results with the community"),
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
                    result = await run_test(tool_name, scenario_name, None, oauth_token_file)
                    analysis = await enhanced_analyze_trace(
                        result["trace"],
                        result.get("scenario_text", ""),
                        result["tool"],
                        oauth_token_file
                    )
                    print_report(result, analysis)
                    
                    # Share result if requested
                    if share:
                        submitter = ResultSubmitter()
                        test_result = TestResult(
                            run_id=result.get("run_id", ""),
                            tool=result["tool"],
                            scenario=result["scenario"],
                            trace=result["trace"],
                            duration=result["duration"],
                            analysis=analysis
                        )
                        await submitter.submit_result(test_result, force=True)
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


# Create community command group
community_app = typer.Typer(help="View and manage community results")
app.add_typer(community_app, name="community")


@community_app.command("stats")
def community_stats(
    tool: Optional[str] = typer.Argument(None, help="Tool to show stats for"),
):
    """View community statistics for tools."""
    typer.echo("Community statistics feature coming soon!")
    typer.echo(f"Will show aggregated results for: {tool or 'all tools'}")
    typer.echo("This will include:")
    typer.echo("  - Success rates across users")
    typer.echo("  - Common friction points")
    typer.echo("  - Tool version compatibility")


@community_app.command("show")
def community_show(
    tool: str = typer.Argument(..., help="Tool name"),
    scenario: str = typer.Argument(..., help="Scenario name"),
    last: int = typer.Option(10, "--last", help="Number of recent results to show"),
):
    """View recent community results for a specific scenario."""
    typer.echo(f"Community results for {tool}/{scenario} (last {last} runs):")
    typer.echo("This feature will show:")
    typer.echo("  - Recent execution results")
    typer.echo("  - Success/failure patterns")
    typer.echo("  - Common issues encountered")


# Create config command group
config_app = typer.Typer(help="Configure AgentProbe settings")
app.add_typer(config_app, name="config")


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key (e.g., sharing.enabled)"),
    value: str = typer.Argument(..., help="Configuration value"),
):
    """Set a configuration value."""
    submitter = ResultSubmitter()
    
    if key == "sharing.enabled":
        enabled = value.lower() in ("true", "yes", "1", "on")
        submitter.enable_sharing(enabled)
    elif key == "sharing.api_key":
        config = submitter._load_config()
        config["api_key"] = value
        submitter.save_config(config)
        typer.echo("[green]API key configured[/green]")
    elif key == "sharing.api_url":
        config = submitter._load_config()
        config["api_url"] = value
        submitter.save_config(config)
        typer.echo(f"[green]API URL set to: {value}[/green]")
    else:
        typer.echo(f"[red]Unknown configuration key: {key}[/red]", err=True)
        typer.echo("Available keys: sharing.enabled, sharing.api_key, sharing.api_url")
        raise typer.Exit(1)


@config_app.command("get")
def config_get(
    key: Optional[str] = typer.Argument(None, help="Configuration key to get"),
):
    """Get configuration values."""
    submitter = ResultSubmitter()
    config = submitter._load_config()
    
    if key:
        # Get specific key
        parts = key.split(".")
        value = config
        for part in parts:
            value = value.get(part, "")
        typer.echo(f"{key}: {value}")
    else:
        # Show all config
        typer.echo("Current configuration:")
        typer.echo(f"  sharing.enabled: {config.get('enabled', False)}")
        typer.echo(f"  sharing.api_url: {config.get('api_url', submitter.DEFAULT_API_URL)}")
        typer.echo(f"  sharing.api_key: {'***' if config.get('api_key') else 'not set'}")
        typer.echo(f"  sharing.anonymous_id: {config.get('anonymous_id', 'not set')}")


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
