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

## What It Does

AgentProbe launches Claude Code to test CLI tools and provides insights on:
- Where agents get confused by your CLI
- Which commands fail and why
- How to improve your CLI's AI-friendliness

## Community Benchmark

Help us build a comprehensive benchmark of CLI tools! The table below shows how well Claude Code handles various CLIs.

| Tool | Scenarios | Passing | Failing | Success Rate | Last Updated |
|------|-----------|---------|---------|--------------|--------------|
| vercel | 5 | 4 | 1 | 80% | 2024-01-20 |
| gh | 8 | 7 | 1 | 87.5% | 2024-01-19 |
| docker | 6 | 5 | 1 | 83.3% | 2024-01-18 |
| npm | 4 | 4 | 0 | 100% | 2024-01-17 |
| git | 10 | 9 | 1 | 90% | 2024-01-16 |
| aws | 3 | 2 | 1 | 66.7% | 2024-01-15 |

[View detailed results →](scenarios/RESULTS.md)

## Commands

### Test Individual Scenarios

```bash
# Test a specific scenario (with uvx)
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe test gh --scenario create-pr

# With custom working directory
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe test docker --scenario run-nginx --work-dir /path/to/project

# Show detailed trace  
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe test gh --scenario create-pr --verbose
```

### Benchmark Tools

```bash
# Test all scenarios for one tool
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe benchmark vercel

# Test all available tools and scenarios
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe benchmark --all
```

### Reports

```bash
# Generate reports (future feature)
uv run agentprobe report --format markdown --output results.md
```

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
  - `deploy.txt` - Deploy applications
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