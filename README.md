# AgentProbe

Test how well AI agents interact with your CLI tools. AgentProbe runs Claude Code against any command-line tool and tells you where it struggles.

## Quick Start

```bash
# No installation needed - run directly with uvx
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe test vercel --scenario deploy

# Or install locally for development
uv sync
uv run agentprobe test vercel --scenario deploy
```

## Authentication

AgentProbe supports multiple authentication methods to avoid environment pollution:

### Get an OAuth Token

First, obtain your OAuth token using Claude Code:

```bash
claude setup-token
```

This will guide you through the OAuth flow and provide a token for authentication.

### Method 1: Token File (Recommended)
```bash
# Store token in a file (replace with your actual token from claude setup-token)
echo "your-oauth-token-here" > ~/.agentprobe-token

# Use with commands
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe test vercel --scenario deploy --oauth-token-file ~/.agentprobe-token
```

### Method 2: Config Files
Create a config file in one of these locations (checked in priority order):

```bash
# Global user config (replace with your actual token from claude setup-token)
mkdir -p ~/.agentprobe
echo "your-oauth-token-here" > ~/.agentprobe/config

# Project-specific config (add to .gitignore)
echo "your-oauth-token-here" > .agentprobe
echo ".agentprobe" >> .gitignore

# Then run normally without additional flags
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe test vercel --scenario deploy
```

### Method 3: Environment Variables (Legacy)
```bash
# Replace with your actual token from claude setup-token
export CLAUDE_CODE_OAUTH_TOKEN="your-oauth-token-here"
# Note: This may affect other Claude CLI processes
```

**Recommendation**: Use token files or config files for better process isolation.

## What It Does

AgentProbe launches Claude Code to test CLI tools and provides insights on:
- Where agents get confused by your CLI
- Which commands fail and why
- How to improve your CLI's AI-friendliness

## Community Benchmark

Help us build a comprehensive benchmark of CLI tools! The table below shows how well Claude Code handles various CLIs.

| Tool | Scenarios | Passing | Failing | Success Rate | Last Updated |
|------|-----------|---------|---------|--------------|--------------|
| vercel | 9 | 7 | 2 | 77.8% | 2025-01-20 |
| gh | 1 | 1 | 0 | 100% | 2025-01-20 |
| docker | 1 | 1 | 0 | 100% | 2025-01-20 |

[View detailed results →](scenarios/RESULTS.md)

## Commands

### Test Individual Scenarios

```bash
# Test a specific scenario (with uvx)
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe test gh --scenario create-pr

# With authentication token file
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe test gh --scenario create-pr --oauth-token-file ~/.agentprobe-token

# With custom working directory
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe test docker --scenario run-nginx --work-dir /path/to/project

# Show detailed trace with message debugging
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe test gh --scenario create-pr --verbose
```

### Benchmark Tools

```bash
# Test all scenarios for one tool
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe benchmark vercel

# Test all scenarios with authentication
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe benchmark vercel --oauth-token-file ~/.agentprobe-token

# Test all available tools and scenarios
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe benchmark --all
```

### Reports

```bash
# Generate reports (future feature)
uv run agentprobe report --format markdown --output results.md
```

### Debugging and Verbose Output

The `--verbose` flag provides detailed insights into how Claude Code interacts with your CLI:

```bash
# Show full message trace with object types and attributes
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe test gh --scenario create-pr --verbose
```

Verbose output includes:
- Message object types (SystemMessage, AssistantMessage, UserMessage, ResultMessage)
- Message content and tool usage
- SDK object attributes and debugging information
- Full conversation trace between Claude and your CLI

## Example Output

```
╭─ AgentProbe Results ─────────────────────────────────────╮
│ Tool: vercel | Scenario: deploy                         │
│ Status: ✓ SUCCESS | Duration: 23.4s | Cost: $0.012     │
│                                                          │
│ Summary:                                                 │
│ • Task completed successfully                            │
│ • Required 3 turns to complete                          │
│                                                          │
│ Observations:                                            │
│ • Agent used help flag to understand the CLI            │
│                                                          │
│ Recommendations:                                         │
│ • Consider improving error messages to be more actionable│
╰──────────────────────────────────────────────────────────╯
```

## Contributing Scenarios

We welcome scenario contributions! Help us test more CLI tools:

1. Fork this repository
2. Add your scenarios under `scenarios/<tool-name>/`
3. Run the tests and update the benchmark table
4. Submit a PR with your results

### Scenario Format

Create simple text files with clear prompts:

```
# scenarios/stripe/create-customer.txt
Create a new Stripe customer with email test@example.com and
add a test credit card. Return the customer ID.
```

### Running Benchmark Tests

```bash
# Test all scenarios for a tool
uv run agentprobe benchmark vercel

# Test all tools
uv run agentprobe benchmark --all

# Generate report (placeholder)
uv run agentprobe report --format markdown
```

## Architecture

AgentProbe follows a simple 4-component architecture:

1. **CLI Layer** (`cli.py`) - Typer-based command interface
2. **Runner** (`runner.py`) - Executes scenarios via Claude Code SDK
3. **Analyzer** (`analyzer.py`) - Generic pattern analysis on execution traces
4. **Reporter** (`reporter.py`) - Rich terminal formatting for results

## Requirements

- Python 3.10+
- uv package manager
- Claude Code SDK (automatically installed)

## Available Scenarios

Current test scenarios included:

- **GitHub CLI** (`gh/`)
  - `create-pr.txt` - Create pull requests
- **Vercel** (`vercel/`)
  - `deploy.txt` - Deploy applications to production
  - `preview-deploy.txt` - Deploy to preview environment
  - `init-project.txt` - Initialize new project with template
  - `env-setup.txt` - Configure environment variables
  - `list-deployments.txt` - List recent deployments
  - `domain-setup.txt` - Add custom domain configuration
  - `rollback.txt` - Rollback to previous deployment
  - `logs.txt` - View deployment logs
  - `build-local.txt` - Build project locally
- **Docker** (`docker/`)
  - `run-nginx.txt` - Run nginx containers

[Browse all scenarios →](scenarios/)

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Format code
uv run black src/

# Lint code
uv run ruff check src/

# Run tests (when implemented)
uv run pytest
```

See [TASKS.md](TASKS.md) for the development roadmap and task tracking.

## Programmatic Usage

```python
import asyncio
from agentprobe import test_cli

async def main():
    result = await test_cli("gh", "create-pr")
    print(f"Success: {result['success']}")
    print(f"Duration: {result['duration_seconds']}s")
    print(f"Cost: ${result['cost_usd']:.3f}")

asyncio.run(main())
```

## License

MIT