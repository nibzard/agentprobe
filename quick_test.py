#!/usr/bin/env python3
"""Quick test of AgentProbe authentication debug logging."""

import asyncio
from pathlib import Path
from src.agentprobe.runner import run_test

async def quick_test():
    """Quick test to see debug output."""
    print("=== AgentProbe Authentication Debug Test ===")
    
    try:
        # Run a simple test
        result = await run_test("gh", "create-pr", None, None)
        print(f"\nTest completed. Success: {result.get('success', 'Unknown')}")
        
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())