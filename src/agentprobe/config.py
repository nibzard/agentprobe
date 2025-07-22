"""Configuration handling for AgentProbe authentication."""

import os
from pathlib import Path
from typing import Optional


def load_oauth_token(oauth_token_file: Optional[Path] = None) -> Optional[str]:
    """Load OAuth token from various sources in priority order.
    
    Priority order:
    1. oauth_token_file parameter (if provided)
    2. ~/.agentprobe/config file
    3. .agentprobe file in current directory
    4. None (fall back to SDK's environment variable detection)
    
    Args:
        oauth_token_file: Optional path to token file
        
    Returns:
        OAuth token string or None
    """
    # 1. Check explicit token file parameter
    if oauth_token_file and oauth_token_file.exists() and oauth_token_file.is_file():
        token = oauth_token_file.read_text().strip()
        if token:
            return token
    
    # 2. Check ~/.agentprobe/config
    home_config = Path.home() / ".agentprobe" / "config"
    if home_config.exists() and home_config.is_file():
        token = home_config.read_text().strip()
        if token:
            return token
    
    # 3. Check local .agentprobe file
    local_config = Path.cwd() / ".agentprobe"
    if local_config.exists() and local_config.is_file():
        token = local_config.read_text().strip()
        if token:
            return token
    
    # 4. Fall back to None (SDK will use environment variables)
    return None


def create_isolated_env(oauth_token: Optional[str] = None) -> dict:
    """Create isolated environment with OAuth token for SDK execution.
    
    Args:
        oauth_token: Optional OAuth token to set
        
    Returns:
        Environment dictionary with isolated OAuth token
    """
    env = os.environ.copy()
    
    if oauth_token:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = oauth_token
    
    return env