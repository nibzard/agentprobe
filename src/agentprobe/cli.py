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
from . import __version__


async def show_community_comparison(tool: str, scenario: str, user_duration: float, user_success: bool) -> None:
    """Show community comparison stats after a test run."""
    try:
        from .community_client import CommunityAPIClient
        
        client = CommunityAPIClient()
        
        # Get scenario-specific stats
        scenario_stats = await client.get_scenario_stats(tool, scenario)
        if not scenario_stats:
            # Fallback to tool stats
            tool_stats = await client.get_tool_stats(tool)
            if tool_stats:
                scenario_stats = tool_stats
            else:
                return  # No community data available
        
        # Extract community metrics
        community_success_rate = scenario_stats.get('success_rate', 0)
        if community_success_rate <= 1:
            community_success_rate *= 100  # Convert to percentage
        
        community_avg_duration = scenario_stats.get('avg_duration', 0)
        total_runs = scenario_stats.get('total_runs', 0)
        
        if total_runs == 0:
            return  # No meaningful data
        
        # Import Rich print for proper markup rendering
        from rich import print as rich_print
        
        # Show comparison
        rich_print(f"\n[dim]🌍 Community Comparison for {tool}/{scenario}:[/dim]")
        
        # Success rate comparison
        success_icon = "✅" if user_success else "❌"
        if user_success:
            if community_success_rate < 100:
                rich_print(f"[green]{success_icon} Success (community avg: {community_success_rate:.0f}%)[/green]")
            else:
                rich_print(f"[green]{success_icon} Success (matches community average)[/green]")
        else:
            if community_success_rate > 0:
                rich_print(f"[red]{success_icon} Failed (community avg: {community_success_rate:.0f}% success)[/red]")
            else:
                rich_print(f"[yellow]{success_icon} Failed (community also struggling with this)[/yellow]")
        
        # Duration comparison  
        if community_avg_duration > 0:
            duration_ratio = user_duration / community_avg_duration
            if duration_ratio < 0.8:
                performance = "[green]faster than average[/green]"
            elif duration_ratio < 1.2:
                performance = "[yellow]average speed[/yellow]"
            else:
                performance = "[red]slower than average[/red]"
            
            rich_print(f"[dim]⏱️  Duration: {user_duration:.1f}s vs {community_avg_duration:.1f}s avg ({performance})[/dim]")
        
        # Show sample size
        rich_print(f"[dim]📊 Based on {total_runs} community runs[/dim]")
        
    except Exception as e:
        # Silently fail - don't disrupt the main test output
        pass

def version_callback(value: bool):
    """Show version information."""
    if value:
        print(f"agentprobe {__version__}")
        raise typer.Exit()

app = typer.Typer(
    name="agentprobe",
    help="Test how well AI agents interact with CLI tools",
    add_completion=False,
)


@app.callback()
def global_options(
    version: bool = typer.Option(
        False, "--version", "-v", 
        callback=version_callback, 
        is_eager=True,
        help="Show version and exit"
    )
):
    """AgentProbe - Test how well AI agents interact with CLI tools."""
    pass


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
                
                # Share result with community (unless opted out)
                submitter = ResultSubmitter()
                test_result = TestResult(
                    run_id=result.get("run_id", ""),
                    tool=result["tool"],
                    scenario=result["scenario"],
                    trace=result["trace"],
                    duration=result["duration_seconds"],
                    analysis=analysis
                )
                await submitter.submit_result(test_result)
                
                # Show community comparison if sharing is enabled
                if submitter.enabled:
                    await show_community_comparison(result["tool"], result["scenario"], result["duration_seconds"], analysis.get('success', False))
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
                    
                    # Share result with community (unless opted out)
                    submitter = ResultSubmitter()
                    test_result = TestResult(
                        run_id=result.get("run_id", ""),
                        tool=result["tool"],
                        scenario=result["scenario"],
                        trace=result["trace"],
                        duration=result["duration_seconds"],
                        analysis=analysis
                    )
                    await submitter.submit_result(test_result)

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
                    
                    # Share result with community (unless opted out)
                    submitter = ResultSubmitter()
                    test_result = TestResult(
                        run_id=result.get("run_id", ""),
                        tool=result["tool"],
                        scenario=result["scenario"],
                        trace=result["trace"],
                        duration=result["duration_seconds"],
                        analysis=analysis
                    )
                    await submitter.submit_result(test_result)
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
    from .community_client import CommunityAPIClient, run_async_command
    
    async def _get_stats():
        client = CommunityAPIClient()
        
        if tool:
            # Show stats for specific tool
            stats = await client.get_tool_stats(tool)
            if stats:
                client.display_tool_stats(stats, tool)
            else:
                print(f"[yellow]No statistics available for {tool} yet.[/yellow]")
                print("[dim]Stats will appear once community members test this tool.[/dim]")
        else:
            # Show leaderboard for all tools
            leaderboard = await client.get_leaderboard()
            if leaderboard:
                client.display_leaderboard(leaderboard)
            else:
                print("[yellow]Community leaderboard not available yet.[/yellow]")
                print("[dim]The leaderboard will appear as more community data is collected.[/dim]")
    
    run_async_command(_get_stats())


@community_app.command("show")
def community_show(
    tool: str = typer.Argument(..., help="Tool name"),
    scenario: str = typer.Argument(..., help="Scenario name"),
    last: int = typer.Option(10, "--last", help="Number of recent results to show"),
):
    """View recent community results for a specific scenario."""
    from .community_client import CommunityAPIClient, run_async_command
    
    async def _show_results():
        client = CommunityAPIClient()
        
        # Get recent results for the scenario
        results = await client.get_recent_results(tool, scenario, last)
        if results:
            client.display_recent_results(results, tool, scenario, last)
        else:
            print(f"[yellow]No recent results found for {tool}/{scenario}.[/yellow]")
            print("[dim]Results will appear as community members test this scenario.[/dim]")
    
    run_async_command(_show_results())


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
        # Legacy support - convert to new opt-out model
        enabled = value.lower() in ("true", "yes", "1", "on")
        submitter.opt_out(not enabled)
    elif key == "sharing.opted_out":
        opted_out = value.lower() in ("true", "yes", "1", "on")
        submitter.opt_out(opted_out)
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
        typer.echo("Available keys:")
        typer.echo("  sharing.opted_out (true/false) - Opt out of community data sharing")
        typer.echo("  sharing.enabled (true/false) - Legacy: Enable/disable sharing")
        typer.echo("  sharing.api_key (string) - Override embedded API key")
        typer.echo("  sharing.api_url (string) - Override API URL")
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
        # Show all config with new opt-in model
        typer.echo("Current configuration:")
        
        # Show sharing status based on new model
        opted_out = config.get('opted_out', False)
        sharing_status = "disabled (opted out)" if opted_out else "enabled"
        typer.echo(f"  sharing.enabled: {not opted_out} ({sharing_status})")
        typer.echo(f"  sharing.opted_out: {opted_out}")
        
        # Show consent status
        consent_given = config.get('consent_given', False)
        if not consent_given:
            typer.echo(f"  sharing.consent_given: {consent_given} (will be asked on next run)")
        else:
            typer.echo(f"  sharing.consent_given: {consent_given}")
        
        # Show API configuration
        using_embedded = not config.get('api_key')
        api_key_status = "embedded key" if using_embedded else "custom key (***)"
        typer.echo(f"  sharing.api_url: {config.get('api_url', submitter.DEFAULT_API_URL)}")
        typer.echo(f"  sharing.api_key: {api_key_status}")
        typer.echo(f"  sharing.anonymous_id: {config.get('anonymous_id', 'not generated yet')}")


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
