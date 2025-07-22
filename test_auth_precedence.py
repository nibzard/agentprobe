#!/usr/bin/env python3
"""Test script to verify Claude Code SDK authentication precedence."""

import os
import asyncio
from claude_code_sdk import query, ClaudeCodeOptions

async def test_auth():
    """Test which authentication method the SDK uses."""
    
    # Show current environment
    print("=== Current Environment ===")
    oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    print(f"CLAUDE_CODE_OAUTH_TOKEN: {'Set' if oauth_token else 'Not set'}")
    if oauth_token:
        print(f"  Token prefix: {oauth_token[:15]}...")
        print(f"  Token length: {len(oauth_token)}")
    
    print(f"ANTHROPIC_API_KEY: {'Set' if api_key else 'Not set'}")
    if api_key:
        print(f"  Key prefix: {api_key[:15]}...")
        print(f"  Key length: {len(api_key)}")
    
    # Test with a simple query
    print("\n=== Testing SDK Authentication ===")
    print("Running simple query: 'What is 2+2?'")
    
    options = ClaudeCodeOptions(
        max_turns=1,
        cwd=None,
        model="sonnet",
    )
    
    try:
        messages = []
        async for message in query(prompt="What is 2+2?", options=options):
            messages.append(message)
        
        # Check result
        if messages:
            final_message = messages[-1]
            if hasattr(final_message, 'subtype'):
                print(f"\nResult: {final_message.subtype}")
            if hasattr(final_message, 'total_cost_usd'):
                print(f"Cost: ${final_message.total_cost_usd:.4f}")
            print("\n✅ SDK call successful!")
            
            # The key insight: If this works with OAuth token set and costs money,
            # then the OAuth token is being used (not API key)
        else:
            print("\n❌ No messages received")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    # First, load the OAuth token from AgentProbe config
    from pathlib import Path
    
    # Try to load from ~/.agentprobe/config
    config_path = Path.home() / ".agentprobe" / "config"
    if config_path.exists() and config_path.is_file():
        oauth_token = config_path.read_text().strip()
        if oauth_token:
            print(f"Loading OAuth token from {config_path}")
            os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = oauth_token
    
    asyncio.run(test_auth())