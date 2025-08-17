"""Result submission module for sharing AgentProbe test results."""

import re
import json
import uuid
import base64
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timezone
import platform
import hashlib

import httpx
from pydantic import BaseModel, Field
from rich import print

from .models import TestResult


# Embedded community API key (obfuscated)
# This key is specific to this release and allows anonymous community data submission
_EMBEDDED_KEY_DATA = "ABc6VxVJQlgHUz5VXwtfEAgKR05nVFEDVVJfU19CSBRZVFQAAVhZD0daXkZObFYABVcCBlRcREIXX1sDawIMVV0TWAhCHD4DCVcEA1BUCxJFQw4BADlUV19URFkPQUxuV1NWAw=="
_OBFUSCATION_KEY = b"agentprobe_community_2024"


def _deobfuscate_key(encoded_data: str, obf_key: bytes) -> str:
    """Deobfuscate the embedded API key."""
    try:
        # Decode base64
        encrypted = base64.b64decode(encoded_data.encode())

        # Simple XOR deobfuscation
        key_len = len(obf_key)
        decrypted = bytearray()
        for i, byte in enumerate(encrypted):
            decrypted.append(byte ^ obf_key[i % key_len])

        return decrypted.decode('utf-8')
    except Exception:
        return ""


def _get_embedded_api_key() -> str:
    """Get the embedded community API key for this release."""
    return _deobfuscate_key(_EMBEDDED_KEY_DATA, _OBFUSCATION_KEY)


class ClientInfo(BaseModel):
    """Information about the client environment."""
    agentprobe_version: str
    os: str
    os_version: str
    python_version: str
    claude_code_version: Optional[str] = None


class ExecutionMetrics(BaseModel):
    """Execution metrics for a test run."""
    duration: float
    total_turns: int
    success: bool
    error_message: Optional[str] = None
    cost: Optional[float] = None


class AnalysisData(BaseModel):
    """Analysis results from a test run."""
    friction_points: list[str] = Field(default_factory=list)
    help_usage_count: int = 0
    retry_count: int = 0
    recommendations: list[str] = Field(default_factory=list)
    agent_summary: Optional[str] = None
    ax_score: Optional[str] = None


class TraceSummary(BaseModel):
    """Sanitized summary of execution trace."""
    commands_executed: list[str] = Field(default_factory=list)
    files_created: list[str] = Field(default_factory=list)
    final_output_snippet: Optional[str] = None


class ResultSubmission(BaseModel):
    """Complete result submission payload."""
    run_id: str
    timestamp: datetime
    tool: str
    scenario: str
    client_info: ClientInfo
    environment: Dict[str, Any]
    execution: ExecutionMetrics
    analysis: AnalysisData
    trace_summary: TraceSummary
    tool_version_info: Optional[Dict[str, Any]] = None


class DataSanitizer:
    """Sanitize sensitive data from test results."""

    # Patterns for sensitive data
    PATTERNS = {
        'api_key': re.compile(r'(api[_-]?key|token|secret|password)[\s:=]+[\w-]+', re.IGNORECASE),
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
        'home_path': re.compile(r'/(?:home|Users)/[^/\s]+'),
        'auth_header': re.compile(r'(Authorization|Bearer)[\s:]+[\w-]+', re.IGNORECASE),
    }

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """Remove sensitive information from text."""
        if not text:
            return text

        # Replace sensitive patterns
        text = cls.PATTERNS['api_key'].sub('[REDACTED_KEY]', text)
        text = cls.PATTERNS['email'].sub('[REDACTED_EMAIL]', text)
        text = cls.PATTERNS['ip_address'].sub('[REDACTED_IP]', text)
        text = cls.PATTERNS['home_path'].sub('/[REDACTED_PATH]', text)
        text = cls.PATTERNS['auth_header'].sub('[REDACTED_AUTH]', text)

        return text

    @classmethod
    def sanitize_list(cls, items: list[str]) -> list[str]:
        """Sanitize a list of strings."""
        return [cls.sanitize_text(item) for item in items]

    @classmethod
    def sanitize_path(cls, path: str) -> str:
        """Sanitize file paths."""
        # Replace home directory with placeholder
        if path.startswith(('/home/', '/Users/')):
            parts = path.split('/', 3)
            if len(parts) > 2:
                return f"/{parts[1]}/[USER]/{parts[3] if len(parts) > 3 else ''}"
        return path


def _is_development_mode() -> bool:
    """Detect if running in development mode (local source) vs production (installed package)."""
    # For now, always use production mode to avoid localhost connection issues
    # This can be re-enabled when local development server is needed
    return False


class ResultSubmitter:
    """Handle submission of test results to the community API."""

    DEFAULT_PRODUCTION_API_URL = "https://agentprobe-community-production.nikola-balic.workers.dev/api/v1"
    DEFAULT_DEVELOPMENT_API_URL = "http://localhost:8787/api/v1"
    CONFIG_FILE = Path.home() / ".agentprobe" / "sharing.json"

    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize the result submitter."""
        config = self._load_config()

        # Choose API URL based on environment
        if api_url:
            self.api_url = api_url
        elif config.get('api_url') and str(config['api_url']).strip():  # Check for non-empty, non-whitespace value
            self.api_url = config['api_url']
        else:
            # Auto-detect development vs production
            if _is_development_mode():
                self.api_url = self.DEFAULT_DEVELOPMENT_API_URL
            else:
                self.api_url = self.DEFAULT_PRODUCTION_API_URL

        # Use embedded community key if no user key configured
        self.api_key = api_key or config.get('api_key') or _get_embedded_api_key()

        # Opt-in by default - check for explicit opt-out
        self.enabled = not config.get('opted_out', False)

        self.include_traces = config.get('include_traces', False)
        self.anonymous_id = self._get_anonymous_id()

    def _load_config(self) -> Dict[str, Any]:
        """Load sharing configuration."""
        if self.CONFIG_FILE.exists():
            try:
                return json.loads(self.CONFIG_FILE.read_text())
            except Exception:
                pass
        return {}

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save sharing configuration."""
        self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.CONFIG_FILE.write_text(json.dumps(config, indent=2))

    def _get_anonymous_id(self) -> str:
        """Get or create anonymous user ID."""
        config = self._load_config()
        if 'anonymous_id' not in config:
            # Generate stable ID based on machine info
            machine_info = f"{platform.node()}{platform.machine()}"
            anonymous_id = hashlib.sha256(machine_info.encode()).hexdigest()[:16]
            config['anonymous_id'] = anonymous_id
            self.save_config(config)
        return config['anonymous_id']

    def _prepare_payload(self, result: TestResult) -> ResultSubmission:
        """Prepare submission payload from test result."""
        # Extract client info
        client_info = ClientInfo(
            agentprobe_version=self._get_version(),
            os=platform.system().lower(),
            os_version=platform.version(),
            python_version=platform.python_version(),
            claude_code_version=self._get_claude_version()
        )

        # Extract execution metrics
        execution = ExecutionMetrics(
            duration=result.duration,
            total_turns=len(result.trace) if result.trace else 0,
            success=result.analysis.get('success', False),
            error_message=DataSanitizer.sanitize_text(
                result.analysis.get('error_message', '')
            ) if result.analysis.get('error_message') else '',
            cost=result.cost_usd
        )

        # Extract friction points from observations (filter out status messages)
        friction_points = []
        for obs in result.analysis.get('observations', []):
            if not obs.startswith("✅") and not obs.startswith("⚠️ Using") and not obs.startswith("⚠️ Claude"):
                friction_points.append(obs)
        
        # Extract analysis data
        analysis = AnalysisData(
            friction_points=DataSanitizer.sanitize_list(friction_points),
            help_usage_count=result.analysis.get('help_usage_count', 0),
            retry_count=result.analysis.get('retry_count', 0),
            recommendations=DataSanitizer.sanitize_list(
                result.analysis.get('recommendations', [])
            ),
            agent_summary=result.analysis.get('ax_summary', result.analysis.get('claude_analysis', None)),
            ax_score=result.analysis.get('ax_score', None)
        )

        # Create sanitized trace summary
        trace_summary = self._create_trace_summary(result)

        # Get tool version info
        tool_version_info = None
        if result.tool_version:
            tool_version_info = {
                'tool_version': result.tool_version,
                'version_detection_method': getattr(result, 'version_detection_method', None),
                'version_detection_success': getattr(result, 'version_detection_success', True)
            }
        
        environment = {
            'anonymous_user_id': self.anonymous_id
        }

        return ResultSubmission(
            run_id=result.run_id if result.run_id else str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            tool=result.tool,
            scenario=result.scenario,
            client_info=client_info,
            environment=environment,
            execution=execution,
            analysis=analysis,
            trace_summary=trace_summary,
            tool_version_info=tool_version_info
        )

    def _create_trace_summary(self, result: TestResult) -> TraceSummary:
        """Create sanitized trace summary."""
        summary = TraceSummary()

        if not self.include_traces or not result.trace:
            return summary

        # Extract commands from trace
        for message in result.trace:
            if message.role == 'assistant' and message.content:
                # Look for command patterns
                lines = message.content.split('\n')
                for line in lines:
                    if line.strip().startswith(('$', '>', '#')) and len(line) > 2:
                        cmd = line.strip().lstrip('$>#').strip()
                        summary.commands_executed.append(
                            DataSanitizer.sanitize_text(cmd)
                        )

        # Sanitize commands
        summary.commands_executed = summary.commands_executed[:10]  # Limit

        # Extract final output
        if result.trace and result.trace[-1].content:
            snippet = result.trace[-1].content[:200]
            summary.final_output_snippet = DataSanitizer.sanitize_text(snippet)

        return summary

    def _get_version(self) -> str:
        """Get AgentProbe version."""
        try:
            from . import __version__
            return __version__
        except ImportError:
            return "unknown"

    def _get_claude_version(self) -> Optional[str]:
        """Get Claude Code SDK version."""
        try:
            import claude_code_sdk
            return getattr(claude_code_sdk, '__version__', None)
        except ImportError:
            return None

    def _get_tool_version(self, tool: str) -> Optional[str]:
        """Get tool version from system."""
        import subprocess
        
        try:
            # Try common version flags
            version_commands = [
                [tool, "--version"],
                [tool, "-v"],
                [tool, "version"],
                [tool, "-V"]
            ]
            
            for cmd in version_commands:
                try:
                    result = subprocess.run(
                        cmd, 
                        capture_output=True, 
                        text=True, 
                        timeout=5
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        # Extract version from output (first line, common patterns)
                        output = result.stdout.strip().split('\n')[0]
                        # Look for version patterns like "tool v1.2.3" or "1.2.3"
                        import re
                        version_match = re.search(r'v?(\d+\.\d+\.\d+)', output)
                        if version_match:
                            return version_match.group(1)
                        # If no pattern match, return the first line (might contain version)
                        return output[:50]  # Limit length
                except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                    continue
                    
            return "unknown"
        except Exception:
            return "unknown"

    async def submit_result(self, result: TestResult, force: bool = False) -> bool:
        """Submit a test result to the API."""
        # Handle first-run consent
        if self.is_first_run():
            consent_given = self.show_consent_dialog()
            # Update enabled status based on consent
            self.enabled = consent_given
            if not consent_given:
                return False

        if not self.enabled and not force:
            return False

        # Validate API URL
        if not self.api_url or not self.api_url.strip():
            print("[red]Error: API URL is not configured[/red]")
            return False

        if not (self.api_url.startswith('http://') or self.api_url.startswith('https://')):
            print(f"[red]Error: Invalid API URL format: {self.api_url}[/red]")
            return False

        try:
            payload = self._prepare_payload(result)
            
            async with httpx.AsyncClient() as client:
                headers = {}
                if self.api_key:
                    # Both local and production agentprobe-community servers use X-API-Key format
                    headers['X-API-Key'] = self.api_key

                response = await client.post(
                    f"{self.api_url}/results",
                    json=payload.model_dump(mode='json'),
                    headers=headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    print("[green]✓ Result shared successfully[/green]")
                    return True
                else:
                    error_text = response.text
                    print(f"[yellow]Failed to share result: {response.status_code}[/yellow]")
                    print(f"[yellow]Error details: {error_text}[/yellow]")
                    return False

        except Exception as e:
            print(f"[red]Error sharing result: {e}[/red]")
            return False

    def opt_out(self, opted_out: bool = True) -> None:
        """Opt out of community data sharing."""
        config = self._load_config()
        config['opted_out'] = opted_out
        self.save_config(config)
        self.enabled = not opted_out

        if opted_out:
            print("[yellow]You have opted out of community data sharing[/yellow]")
            print("[dim]Your test results will only be stored locally[/dim]")
        else:
            print("[green]Community data sharing is now enabled[/green]")
            print("[dim]Anonymous test results will help improve CLI tools for AI agents[/dim]")

    def enable_sharing(self, enabled: bool = True) -> None:
        """Enable or disable result sharing (legacy method)."""
        # Convert to new opt-out model
        self.opt_out(not enabled)

    def is_first_run(self) -> bool:
        """Check if this is the first run (no consent given yet)."""
        config = self._load_config()
        return not config.get('consent_given', False)

    def show_consent_dialog(self) -> bool:
        """Show consent dialog for first-time users. Returns True if user consents."""
        print("\n[bold blue]🤖 Welcome to AgentProbe![/bold blue]")
        print()
        print("[dim]AgentProbe collects anonymous usage data to improve CLI tools for AI agents.[/dim]")
        print("[dim]This helps identify common friction points and success patterns.[/dim]")
        print()
        print("[green]✓ Data is anonymized and sanitized[/green]")
        print("[green]✓ No personal information is collected[/green]")
        print("[green]✓ You can opt out anytime with: agentprobe config set sharing.opted_out true[/green]")
        print()
        print("[dim]Learn more: https://github.com/nibzard/agentprobe#privacy[/dim]")
        print()

        try:
            while True:
                response = input("Share anonymous data to help improve CLI tools? [Y/n]: ").strip().lower()
                if response in ['', 'y', 'yes']:
                    # User consents - save this choice
                    config = self._load_config()
                    config['opted_out'] = False
                    config['consent_given'] = True
                    self.save_config(config)
                    print("[green]Thank you! Your anonymous data will help improve CLI tools for everyone.[/green]")
                    return True
                elif response in ['n', 'no']:
                    # User opts out
                    config = self._load_config()
                    config['opted_out'] = True
                    config['consent_given'] = True
                    self.save_config(config)
                    print("[yellow]No problem! AgentProbe will work locally without sharing data.[/yellow]")
                    return False
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
        except (EOFError, KeyboardInterrupt):
            # Non-interactive environment or user interrupted - default to consent
            config = self._load_config()
            config['opted_out'] = False
            config['consent_given'] = True
            self.save_config(config)
            print("\n[green]Proceeding with anonymous data sharing to help improve CLI tools.[/green]")
            print("[dim]You can opt out anytime with: agentprobe config set sharing.opted_out true[/dim]")
            return True