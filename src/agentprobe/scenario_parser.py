"""Parse scenario files with optional YAML frontmatter."""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import re


def parse_scenario(file_path: Path) -> Dict[str, Any]:
    """Parse a scenario file with optional YAML frontmatter.
    
    Returns a dict with:
    - content: The actual scenario prompt
    - metadata: Dict of YAML frontmatter (if present)
    """
    content = file_path.read_text()
    
    # Check for YAML frontmatter
    if content.startswith('---\n'):
        # Find the closing ---
        match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
        if match:
            yaml_content = match.group(1)
            scenario_content = match.group(2).strip()
            
            try:
                metadata = yaml.safe_load(yaml_content) or {}
            except yaml.YAMLError:
                # If YAML parsing fails, treat entire file as content
                metadata = {}
                scenario_content = content
        else:
            # No closing ---, treat entire file as content
            metadata = {}
            scenario_content = content
    else:
        # No frontmatter
        metadata = {}
        scenario_content = content.strip()
    
    return {
        'content': scenario_content,
        'metadata': metadata
    }


def get_scenario_options(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Extract Claude Code SDK options from scenario metadata.
    
    Returns options that can be used to override ClaudeCodeOptions.
    """
    options = {}
    
    # Map metadata fields to SDK options
    if 'model' in metadata:
        options['model'] = metadata['model']
    
    if 'allowed_tools' in metadata:
        options['allowed_tools'] = metadata['allowed_tools']
    
    if 'permission_mode' in metadata:
        options['permission_mode'] = metadata['permission_mode']
    
    return options