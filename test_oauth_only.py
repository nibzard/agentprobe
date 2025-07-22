#!/usr/bin/env python3
"""Test script to verify OAuth-only authentication."""

import os
import asyncio
from claude_code_sdk import query, ClaudeCodeOptions

async def test_oauth_only():
    """Test SDK with ONLY OAuth token (no API key)."""
    
    # Load OAuth token
    from pathlib import Path
    config_path = Path.home() / ".agentprobe" / "config"
    if config_path.exists() and config_path.is_file():
        oauth_token = config_path.read_text().strip()
        if oauth_token:
            os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = oauth_token
    
    # REMOVE API key from environment
    if "ANTHROPIC_API_KEY" in os.environ:
        print("Removing ANTHROPIC_API_KEY from environment")
        del os.environ["ANTHROPIC_API_KEY"]
    
    # Show current environment
    print("=== OAuth-Only Environment ===")
    oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    print(f"CLAUDE_CODE_OAUTH_TOKEN: {'Set' if oauth_token else 'Not set'}")
    if oauth_token:
        print(f"  Token prefix: {oauth_token[:15]}...")
        print(f"  Token length: {len(oauth_token)}")
    
    print(f"ANTHROPIC_API_KEY: {'Set' if api_key else 'Not set'}")
    
    # Test with a simple query
    print("\n=== Testing OAuth-Only Authentication ===")
    print("Running simple query: 'What is the capital of France?'")
    
    options = ClaudeCodeOptions(
        max_turns=1,
        cwd=None,
        model="sonnet",
    )
    
    try:
        messages = []
        async for message in query(prompt="What is the capital of France?", options=options):
            messages.append(message)
        
        # Check result
        if messages:
            final_message = messages[-1]
            if hasattr(final_message, 'subtype'):
                print(f"\nResult: {final_message.subtype}")
            if hasattr(final_message, 'total_cost_usd'):
                print(f"Cost: ${final_message.total_cost_usd:.4f}")
            print("\n✅ OAuth token working correctly!")
        else:
            print("\n❌ No messages received")
            
    except Exception as e:
        print(f"\n❌ Error with OAuth-only: {e}")
        print(f"Error type: {type(e).__name__}")
        print("This suggests OAuth token may be invalid or SDK prefers API key")

if __name__ == "__main__":
    asyncio.run(test_oauth_only())