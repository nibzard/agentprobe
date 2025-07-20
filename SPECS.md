# AgentProbe Specification

## Overview

AgentProbe is a Python-based CLI testing harness that launches Claude Code non-interactively to test how well AI agents interact with command-line tools. It records execution traces, analyzes patterns, and generates actionable recommendations for improving CLI usability. Distributed via Astral's uv/uvx for instant, install-free execution.

### Core Value Proposition
- **Tool-Agnostic**: Test any CLI tool without modifying AgentProbe's core
- **Simple Scenarios**: Plain text prompts, no complex configuration
- **Reproducible Testing**: Consistent test execution across environments
- **Actionable Insights**: Identify where agents struggle with your CLI

## Installation

### Quick Start (No Installation Required)
```bash
# Run directly with uvx
uvx agentprobe test vercel --scenario deploy

# Or install uv first if needed
curl -sSf https://astral.sh/uv/install | sh
```

### Local Installation
```bash
pip install agentprobe
```

### Requirements
- Python ≥ 3.10
- Claude Code CLI: `npm install -g @anthropic-ai/claude-code`
- Target CLI tool (e.g., vercel, gh, docker)

## Usage

AgentProbe uses a simple command structure:

```bash
agentprobe test <tool> --scenario <name>
```

Examples:
```bash
# Test Vercel deployment
agentprobe test vercel --scenario deploy

# Test GitHub CLI PR creation
agentprobe test gh --scenario create-pr

# Test Docker container management
agentprobe test docker --scenario run-nginx
```

## Scenarios

Scenarios are plain text files containing prompts for Claude. No YAML, no configuration - just the task description.

### Example: `scenarios/vercel/deploy.txt`
```
Deploy this Next.js application to production using Vercel CLI.
Make sure the deployment is successful and return the deployment URL.
```

### Example: `scenarios/gh/create-pr.txt`
```
Create a pull request for the current branch with a descriptive title
and summary of the changes.
```

### Custom Scenarios
Create your own scenarios by adding text files:
```bash
mkdir -p scenarios/mycli
echo "Run mycli init and configure it for production use" > scenarios/mycli/setup.txt
agentprobe test mycli --scenario setup
```

## Architecture

### Simple Execution Flow
```python
async def run_test(tool: str, scenario_name: str):
    # 1. Load scenario prompt
    prompt = read_file(f"scenarios/{tool}/{scenario_name}.txt")

    # 2. Execute with Claude Code SDK
    trace = []
    async for message in query(prompt=prompt, options=default_options):
        trace.append(message)

    # 3. Analyze and report
    analysis = analyze_trace(trace)
    print_report(analysis)
```

### Core Components

1. **CLI** (`cli.py`) - Simple command-line interface using Typer
2. **Runner** (`runner.py`) - Executes scenarios via Claude Code SDK
3. **Analyzer** (`analyzer.py`) - Generic analysis of execution traces
4. **Reporter** (`reporter.py`) - Formats results for terminal output

### Package Structure
```
agentprobe/
├── __init__.py
├── cli.py          # Command-line interface
├── runner.py       # Claude Code SDK integration
├── analyzer.py     # Trace analysis
├── reporter.py     # Output formatting
└── scenarios/      # Example scenarios
    ├── vercel/
    │   ├── deploy.txt
    │   ├── dev.txt
    │   └── rollback.txt
    ├── gh/
    │   ├── create-pr.txt
    │   └── clone.txt
    └── docker/
        ├── build.txt
        └── run.txt
```

## Analysis

AgentProbe performs generic analysis applicable to any CLI:

### Detected Patterns
- **Command Success/Failure** - Did the CLI commands execute successfully?
- **Error Recovery** - How did the agent handle errors?
- **Help Usage** - Did the agent use `--help` when stuck?
- **Flag Discovery** - Were the correct flags identified?
- **Interactive Handling** - How were prompts handled?

### Example Output
```
╭─ AgentProbe Results ─────────────────────────────────────╮
│ Tool: vercel | Scenario: deploy                         │
│ Status: ✓ SUCCESS | Duration: 23.4s | Cost: $0.012     │
├──────────────────────────────────────────────────────────┤
│ Summary:                                                 │
│ • Successfully deployed to https://app-xi.vercel.app     │
│ • Required 5 turns to complete                          │
│ • No authentication errors encountered                  │
├──────────────────────────────────────────────────────────┤
│ Observations:                                            │
│ • Agent needed 2 attempts to find correct deploy flag   │
│ • Help command was used effectively                     │
│ • Output parsing was accurate                           │
╰──────────────────────────────────────────────────────────╯
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--scenario` | Scenario name | Required |
| `--work-dir` | Working directory | Current dir |
| `--max-turns` | Max agent interactions | 20 |
| `--verbose` | Show detailed trace | False |
| `--output` | Output format (text/json) | text |

## Python API

```python
import asyncio
from agentprobe import test_cli

async def main():
    result = await test_cli(
        tool="vercel",
        scenario="deploy",
        work_dir="/path/to/project"
    )

    print(f"Success: {result.success}")
    print(f"Duration: {result.duration_seconds}s")
    print(f"Cost: ${result.cost_usd}")

asyncio.run(main())
```

## Extending AgentProbe

### Adding New CLI Tools
1. Create a directory under `scenarios/`
2. Add text files with prompts
3. Run tests - no code changes needed

### Custom Analysis
While AgentProbe's analysis is generic, you can extend it:

```python
from agentprobe import run_test, analyze_trace

# Run test and get raw trace
trace = await run_test("mycli", "scenario")

# Custom analysis
my_analysis = my_custom_analyzer(trace)
```

## Configuration

AgentProbe uses minimal configuration via environment variables:

```bash
# Claude Code settings
export ANTHROPIC_API_KEY=sk-...
export AGENTPROBE_MAX_TURNS=30

# Optional: Custom scenarios directory
export AGENTPROBE_SCENARIOS_DIR=/path/to/scenarios
```

## Roadmap

### Phase 1 (Current)
- [ ] Core execution engine
- [ ] Simple scenario format
- [ ] Basic analysis
- [ ] Package release

### Phase 2
- [ ] Parallel test execution
- [ ] Comparison reports (multiple runs)
- [ ] Cost optimization features
- [ ] CI/CD integration examples

### Phase 3
- [ ] Web dashboard for results
- [ ] Scenario sharing platform
- [ ] Multi-model support (GPT-4, local models)

## Design Principles

1. **Simplicity First** - Plain text scenarios, minimal configuration
2. **Tool Agnostic** - No tool-specific code in core
3. **Extensible** - Easy to add new CLIs without code changes
4. **Practical** - Focus on real-world CLI testing needs

## Security

- Never include credentials in scenarios
- Run tests in isolated environments
- AgentProbe doesn't provide sandboxing
- Review Claude's actions with `--verbose` flag

## Contributing

We welcome contributions:
- New example scenarios for popular CLIs
- Bug reports and feature requests
- Documentation improvements

## License

MIT License - See LICENSE file for details.