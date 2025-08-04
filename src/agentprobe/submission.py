"""Result submission module for sharing AgentProbe test results."""

import os
import re
import json
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timezone
import platform
import hashlib

import httpx
from pydantic import BaseModel, Field
from rich import print

from .models import TestResult


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
    cost: Optional[Dict[str, Any]] = None


class AnalysisData(BaseModel):
    """Analysis results from a test run."""
    friction_points: list[str] = Field(default_factory=list)
    help_usage_count: int = 0
    retry_count: int = 0
    recommendations: list[str] = Field(default_factory=list)


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


class ResultSubmitter:
    """Handle submission of test results to the community API."""
    
    DEFAULT_API_URL = "https://api.agentprobe.dev/v1"
    CONFIG_FILE = Path.home() / ".agentprobe" / "sharing.json"
    
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize the result submitter."""
        self.api_url = api_url or self._load_config().get('api_url', self.DEFAULT_API_URL)
        self.api_key = api_key or self._load_config().get('api_key')
        self.enabled = self._load_config().get('enabled', False)
        self.include_traces = self._load_config().get('include_traces', False)
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
                result.analysis.get('error_message')
            ) if result.analysis.get('error_message') else None,
            cost=result.analysis.get('cost')
        )
        
        # Extract analysis data
        analysis = AnalysisData(
            friction_points=result.analysis.get('friction_points', []),
            help_usage_count=result.analysis.get('help_usage_count', 0),
            retry_count=result.analysis.get('retry_count', 0),
            recommendations=DataSanitizer.sanitize_list(
                result.analysis.get('recommendations', [])
            )
        )
        
        # Create sanitized trace summary
        trace_summary = self._create_trace_summary(result)
        
        # Get tool version
        environment = {
            'tool_version': self._get_tool_version(result.tool),
            'anonymous_user_id': self.anonymous_id
        }
        
        return ResultSubmission(
            run_id=result.run_id,
            timestamp=datetime.now(timezone.utc),
            tool=result.tool,
            scenario=result.scenario,
            client_info=client_info,
            environment=environment,
            execution=execution,
            analysis=analysis,
            trace_summary=trace_summary
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
        # This would be implemented to check tool versions
        # For now, return placeholder
        return "unknown"
    
    async def submit_result(self, result: TestResult, force: bool = False) -> bool:
        """Submit a test result to the API."""
        if not self.enabled and not force:
            return False
        
        try:
            payload = self._prepare_payload(result)
            
            async with httpx.AsyncClient() as client:
                headers = {}
                if self.api_key:
                    headers['Authorization'] = f"Bearer {self.api_key}"
                
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
                    print(f"[yellow]Failed to share result: {response.status_code}[/yellow]")
                    return False
                    
        except Exception as e:
            print(f"[red]Error sharing result: {e}[/red]")
            return False
    
    def enable_sharing(self, enabled: bool = True) -> None:
        """Enable or disable result sharing."""
        config = self._load_config()
        config['enabled'] = enabled
        self.save_config(config)
        self.enabled = enabled
        
        status = "enabled" if enabled else "disabled"
        print(f"[green]Result sharing {status}[/green]")