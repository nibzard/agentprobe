"""Community API client for fetching statistics and results."""

import asyncio
from typing import Optional, Dict, Any, List
import httpx
from rich import print
from rich.table import Table
from rich.console import Console

from .submission import _get_embedded_api_key


class CommunityAPIClient:
    """Client for interacting with the AgentProbe community API."""
    
    def __init__(self, api_url: str = "https://agentprobe-community-production.nikola-balic.workers.dev/api/v1"):
        self.api_url = api_url
        self.api_key = _get_embedded_api_key()
        self.console = Console()
    
    async def get_tool_stats(self, tool: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific tool."""
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = await client.get(
                    f"{self.api_url}/stats/tool/{tool}",
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Extract the actual data from the API response
                    return data.get("data", {}) if isinstance(data, dict) else data
                else:
                    print(f"[yellow]Could not fetch stats for {tool}: {response.status_code}[/yellow]")
                    return None
        except Exception as e:
            print(f"[red]Error fetching tool stats: {e}[/red]")
            return None
    
    async def get_leaderboard(self) -> Optional[List[Dict[str, Any]]]:
        """Get the community leaderboard."""
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = await client.get(
                    f"{self.api_url}/leaderboard",
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Extract the actual data array from the API response
                    return data.get("data", []) if isinstance(data, dict) else data
                else:
                    print(f"[yellow]Could not fetch leaderboard: {response.status_code}[/yellow]")
                    return None
        except Exception as e:
            print(f"[red]Error fetching leaderboard: {e}[/red]")
            return None
    
    async def get_scenario_stats(self, tool: str, scenario: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific scenario."""
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = await client.get(
                    f"{self.api_url}/stats/scenario/{tool}/{scenario}",
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Extract the actual data from the API response
                    return data.get("data", {}) if isinstance(data, dict) else data
                else:
                    print(f"[yellow]Could not fetch scenario stats: {response.status_code}[/yellow]")
                    return None
        except Exception as e:
            print(f"[red]Error fetching scenario stats: {e}[/red]")
            return None
    
    async def get_recent_results(self, tool: str, scenario: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Get recent results for a specific tool/scenario."""
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = await client.get(
                    f"{self.api_url}/results",
                    headers=headers,
                    params={"tool": tool, "scenario": scenario, "limit": limit},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json().get("results", [])
                else:
                    print(f"[yellow]Could not fetch recent results: {response.status_code}[/yellow]")
                    return None
        except Exception as e:
            print(f"[red]Error fetching recent results: {e}[/red]")
            return None
    
    def display_tool_stats(self, stats: Dict[str, Any], tool: str) -> None:
        """Display tool statistics in a formatted table."""
        print(f"\n[bold blue]📊 Community Statistics for {tool.upper()}[/bold blue]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        
        if "success_rate" in stats:
            # Handle both percentage (0-100) and decimal (0-1) formats
            success_rate = stats['success_rate']
            if success_rate <= 1:
                success_rate *= 100  # Convert from decimal to percentage
            table.add_row("Success Rate", f"{success_rate:.1f}%")
        if "total_runs" in stats:
            table.add_row("Total Runs", str(stats['total_runs']))
        if "avg_duration" in stats:
            table.add_row("Avg Duration", f"{stats['avg_duration']:.1f}s")
        if "avg_turns" in stats:
            table.add_row("Avg Turns", f"{stats['avg_turns']:.1f}")
        
        self.console.print(table)
        
        # Show common friction points if available
        if "friction_points" in stats and stats["friction_points"]:
            print(f"\n[bold yellow]⚠️  Common Friction Points:[/bold yellow]")
            for point in stats["friction_points"][:5]:  # Show top 5
                print(f"  • {point}")
    
    def display_leaderboard(self, leaderboard: List[Dict[str, Any]]) -> None:
        """Display the community leaderboard."""
        print(f"\n[bold blue]🏆 Community Leaderboard[/bold blue]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Rank", justify="right", style="bold")
        table.add_column("Tool", style="cyan")
        table.add_column("Success Rate", justify="right")
        table.add_column("Total Runs", justify="right")
        table.add_column("Avg Duration", justify="right")
        
        for i, entry in enumerate(leaderboard[:10], 1):  # Show top 10
            rank_style = "gold1" if i == 1 else "silver" if i == 2 else "yellow4" if i == 3 else "white"
            
            # Handle success rate format (decimal to percentage)
            success_rate = entry.get('success_rate', 0)
            if success_rate <= 1:
                success_rate *= 100
            
            table.add_row(
                str(i),
                entry.get("tool", "Unknown"),
                f"{success_rate:.1f}%",
                str(entry.get('total_runs', 0)),
                f"{entry.get('avg_duration', 0):.1f}s",
                style=rank_style
            )
        
        self.console.print(table)
    
    def display_recent_results(self, results: List[Dict[str, Any]], tool: str, scenario: str, limit: int) -> None:
        """Display recent results for a specific scenario."""
        print(f"\n[bold blue]📝 Recent Results for {tool}/{scenario}[/bold blue]")
        
        if not results:
            print("[yellow]No recent results found for this scenario.[/yellow]")
            print("[dim]Results will appear as community members test this scenario.[/dim]")
            return
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Date", style="cyan")
        table.add_column("Success", justify="center")
        table.add_column("Duration", justify="right")
        table.add_column("Turns", justify="right")
        table.add_column("Notes")
        
        for result in results[:limit]:
            success_icon = "✅" if result.get("execution", {}).get("success", False) else "❌"
            success_style = "green" if result.get("execution", {}).get("success", False) else "red"
            
            # Format timestamp
            timestamp = result.get("timestamp", "")
            date_str = timestamp.split("T")[0] if timestamp else "Unknown"
            
            duration = result.get("execution", {}).get("duration", 0)
            turns = result.get("execution", {}).get("total_turns", 0)
            
            # Get a brief note from analysis
            friction_points = result.get("analysis", {}).get("friction_points", [])
            note = friction_points[0] if friction_points else "No issues"
            
            table.add_row(
                date_str,
                success_icon,
                f"{duration:.1f}s",
                str(turns),
                note[:40] + "..." if len(note) > 40 else note,
                style=success_style if not friction_points else "yellow"
            )
        
        self.console.print(table)
        
        # Show success rate summary
        successful = sum(1 for r in results if r.get("execution", {}).get("success", False))
        total = len(results)
        success_rate = (successful / total * 100) if total > 0 else 0
        
        print(f"\n[bold]Summary:[/bold] {successful}/{total} successful ({success_rate:.1f}% success rate)")


def run_async_command(coro):
    """Helper to run async commands in CLI context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)