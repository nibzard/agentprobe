"""Data models for AgentProbe."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class TestResult:
    """Result of a test run."""
    run_id: str
    tool: str
    scenario: str
    trace: List[Any]  # List of messages from Claude Code SDK
    duration: float
    analysis: Dict[str, Any]
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)