# AgentProbe

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/nibzard/agentprobe.svg)](https://github.com/nibzard/agentprobe)
[![GitHub Issues](https://img.shields.io/github/issues/nibzard/agentprobe.svg)](https://github.com/nibzard/agentprobe/issues)

Test how well AI agents interact with your CLI tools. AgentProbe runs Claude Code against any command-line tool and provides actionable insights to improve Agent Experience (AX) - helping CLI developers make their tools more AI-friendly.

<p align="center">
  <img src="assets/agentprobe.jpeg" alt="AgentProbe" width="100%">
</p>

## Quick Start

```bash
# No installation needed - run directly with uvx
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe test vercel --scenario deploy

# Or install locally for development
uv sync
uv run agentprobe test git --scenario status
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

AgentProbe launches Claude Code to test CLI tools and provides **Agent Experience (AX)** insights on:
- **AX Score** (A-F) based on turn count and success rate
- **CLI Friction Points** - specific issues that confuse agents
- **Actionable Improvements** - concrete changes to reduce agent friction
- **Real-time Progress** - see agent progress with live turn counts

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

# Test multiple runs for consistency analysis
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe test vercel --scenario deploy --runs 5

# With custom working directory
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe test docker --scenario run-nginx --work-dir /path/to/project

# Show detailed trace with message debugging (disables progress indicators)
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe test gh --scenario create-pr --verbose

# ⚠️ DANGEROUS: Run without permission prompts (use only in safe environments)
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe test docker --scenario run-nginx --yolo
```

### Benchmark Tools

```bash
# Test all scenarios for one tool
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe benchmark vercel

# Test all scenarios with authentication
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe benchmark vercel --oauth-token-file ~/.agentprobe-token

# Test all available tools and scenarios
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe benchmark --all

# ⚠️ DANGEROUS: Run all benchmarks without permission prompts
uvx --from git+https://github.com/nibzard/agentprobe.git agentprobe benchmark --all --yolo
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

### ⚠️ YOLO Mode (Use with Extreme Caution)

The `--yolo` flag enables autonomous execution without permission prompts, allowing Claude to run ANY command without user approval:

```bash
# WARNING: Only use in isolated, safe environments
agentprobe test docker --scenario build-app --yolo
```

**Security Considerations:**
- **ONLY** use in containerized or sandboxed environments
- Claude can execute arbitrary commands including `rm -rf`, network calls, system modifications
- No safety guardrails - Claude has full system access
- Intended for CI/CD pipelines, testing environments, or research purposes
- **NEVER** use on production systems or with sensitive data

This mode is equivalent to running Claude Code with `--dangerously-skip-permissions`.

## Example Output

### Single Run (Default)
```
⠋ Agent running... (Turn 3, 12s)
╭───────────────────────────── AgentProbe Results ─────────────────────────────╮
│ Tool: vercel | Scenario: deploy                                               │
│ AX Score: B (12 turns, 80% success rate)                                      │
│                                                                               │
│ Agent Experience Summary:                                                     │
│ Agent completed deployment but needed extra turns due to unclear progress     │
│ feedback and ambiguous success indicators.                                    │
│                                                                               │
│ CLI Friction Points:                                                          │
│ • No progress feedback during build process                                   │
│ • Deployment URL returned before actual completion                            │
│ • Success status ambiguous ("building" vs "deployed")                        │
│                                                                               │
│ Top Improvements for CLI:                                                     │
│ 1. Add --status flag to check deployment progress                             │
│ 2. Include completion status in deployment output                             │
│ 3. Provide structured --json output for programmatic usage                    │
│                                                                               │
│ Expected turns: 5-8 | Duration: 23.4s | Cost: $0.012                         │
│                                                                               │
│ Use --verbose for full trace analysis                                         │
╰───────────────────────────────────────────────────────────────────────────────╯
```

### Multiple Runs (Aggregate)
```
╭──────────────────────── AgentProbe Aggregate Results ────────────────────────╮
│ Tool: vercel | Scenario: deploy                                               │
│ AX Score: C (14.2 avg turns, 60% success rate) | Runs: 5                      │
│                                                                               │
│ Consistency Analysis:                                                         │
│ • Turn variance: 8-22 turns                                                   │
│ • Success consistency: 60% of runs succeeded                                  │
│ • Agent confusion points: 18 total friction events                            │
│                                                                               │
│ Consistent CLI Friction Points:                                               │
│ • Permission errors lack clear remediation steps                              │
│ • No progress feedback during deployment                                      │
│ • Build failures don't suggest next steps                                     │
│                                                                               │
│ Priority Improvements for CLI:                                                │
│ 1. Add deployment status polling with vercel status                           │
│ 2. Include troubleshooting hints in error messages                            │
│ 3. Provide progress indicators during long operations                          │
│                                                                               │
│ Avg duration: 45.2s | Total cost: $0.156                                      │
╰───────────────────────────────────────────────────────────────────────────────╯
```

## Contributing Scenarios

We welcome scenario contributions! Help us test more CLI tools:

1. Fork this repository
2. Add your scenarios under `scenarios/<tool-name>/`
3. Run the tests and update the benchmark table
4. Submit a PR with your results

### Scenario Format

#### Simple Text Format
Create simple text files with clear prompts:

```
# scenarios/stripe/create-customer.txt
Create a new Stripe customer with email test@example.com and
add a test credit card. Return the customer ID.
```

#### Enhanced YAML Format (Recommended)
Use YAML frontmatter for better control and metadata:

```yaml
# scenarios/vercel/deploy-complex.txt
---
version: 2
created: 2025-01-22
tool: vercel
permission_mode: acceptEdits
allowed_tools: [Read, Write, Bash]
model: opus
max_turns: 15
complexity: complex
expected_turns: 8-12
description: "Production deployment with environment setup"
---
Deploy this Next.js application to production using Vercel CLI.
Configure production environment variables and ensure the deployment
is successful with proper domain configuration.
```

**YAML Frontmatter Options:**
- `model`: Override default model (`sonnet`, `opus`)
- `max_turns`: Limit agent interactions
- `permission_mode`: Set permissions (`acceptEdits`, `default`, `plan`, `bypassPermissions`)
- `allowed_tools`: Specify tools (`[Read, Write, Bash]`)
- `expected_turns`: Range for AX scoring comparison
- `complexity`: Scenario difficulty (`simple`, `medium`, `complex`)

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

1. **CLI Layer** (`cli.py`) - Typer-based command interface with progress indicators
2. **Runner** (`runner.py`) - Executes scenarios via Claude Code SDK with YAML frontmatter support
3. **Analyzer** (`analyzer.py`) - AI-powered analysis using Claude to identify friction points
4. **Reporter** (`reporter.py`) - AX-focused output for CLI developers

### Agent Experience (AX) Analysis

AgentProbe uses Claude itself to analyze agent interactions, providing:

- **Intelligent Analysis**: Claude analyzes execution traces to identify specific friction points
- **AX Scoring**: Automatic scoring based on turn efficiency and success patterns
- **Contextual Recommendations**: Actionable improvements tailored to each CLI tool
- **Consistency Tracking**: Multi-run analysis to identify systematic issues

This approach avoids hardcoded patterns and provides nuanced, tool-specific insights that help CLI developers understand exactly where their tools create friction for AI agents.

### Prompt Management & Versioning

AgentProbe uses externalized Jinja2 templates for analysis prompts:

- **Template-based Prompts**: Analysis prompts are stored in `prompts/analysis.jinja2` for easy editing and iteration
- **Version Tracking**: Each analysis includes prompt version metadata for reproducible results
- **Dynamic Variables**: Templates support contextual variables (scenario, tool, trace data)
- **Historical Comparison**: Version tracking enables comparing results across prompt iterations

```bash
# Prompt templates are automatically loaded from prompts/ directory
# Version information is tracked in prompts/metadata.json
# Analysis results include prompt_version field for tracking
```

## Requirements

- Python 3.10+
- uv package manager
- Claude Code SDK (automatically installed)

## Key Features

### 🎯 Agent Experience (AX) Focus
- **AX Scores** (A-F) based on turn efficiency and success rate
- **Friction Point Analysis** identifies specific CLI pain points
- **Actionable Recommendations** for CLI developers

### 📊 Progress & Feedback
- **Real-time Progress** with live turn count and elapsed time
- **Consistency Analysis** across multiple runs
- **Expected vs Actual** turn comparison using YAML metadata

### 🔧 Advanced Scenario Control
- **YAML Frontmatter** for model selection, permissions, turn limits
- **Multiple Authentication** methods with process isolation
- **Flexible Tool Configuration** per scenario

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
  - `ax-test.txt` - Simple version check (AX demo)
  - `yaml-options-test.txt` - YAML frontmatter demo
- **Docker** (`docker/`)
  - `run-nginx.txt` - Run nginx containers
- **Wrangler (Cloudflare)** (`wrangler/`)
  - Multiple deployment and development scenarios

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