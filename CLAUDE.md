# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgentProbe is a generic CLI testing harness that uses Claude Code SDK to test how well AI agents interact with command-line tools. It runs scenarios (simple text prompts) against CLIs and analyzes the results to provide insights on CLI usability for AI agents.

## Core Architecture

The project follows a simple 4-component architecture:

1. **CLI Layer** (`cli.py`) - Typer-based command interface with three main commands: `test`, `benchmark`, `report`
2. **Runner** (`runner.py`) - Executes scenarios via Claude Code SDK, handles the async message stream, and extracts results
3. **Analyzer** (`analyzer.py`) - Generic pattern analysis on execution traces (error detection, help usage, success/failure)
4. **Reporter** (`reporter.py`) - Rich terminal formatting for results display

The execution flow: Load scenario text → Execute via Claude Code SDK → Analyze trace → Format output

## Development Commands

```bash
# Install dependencies (uses uv)
uv sync

# Install with dev dependencies
uv sync --extra dev

# Run the CLI locally
uv run agentprobe test vercel --scenario deploy

# Run tests (when implemented)
uv run pytest

# Format code
uv run black src/

# Lint code
uv run ruff check src/
```

## Scenario System

Scenarios are stored as plain text files in `scenarios/<tool>/<name>.txt` containing only the prompt for Claude. No YAML, no configuration - just the task description. This is a core design principle to keep the system simple and tool-agnostic.

Examples:
- `scenarios/vercel/deploy.txt` - "Deploy this Next.js application to production..."
- `scenarios/gh/create-pr.txt` - "Create a pull request for the current branch..."

## Authentication

AgentProbe supports multiple authentication methods to avoid polluting the global environment:

### Method 1: Token File (Recommended)
Use the `--oauth-token-file` parameter to specify a file containing your OAuth token:

```bash
# Store token in a file
echo "your-oauth-token-here" > ~/.agentprobe-token

# Use with agentprobe
uv run agentprobe test vercel --scenario deploy --oauth-token-file ~/.agentprobe-token
uv run agentprobe benchmark --all --oauth-token-file ~/.agentprobe-token
```

### Method 2: Config File
Create a config file in one of these locations (checked in priority order):

1. `~/.agentprobe/config` - Global user config
2. `.agentprobe` - Project-specific config (add to .gitignore)

```bash
# Global config
mkdir -p ~/.agentprobe
echo "your-oauth-token-here" > ~/.agentprobe/config

# Project-specific config
echo "your-oauth-token-here" > .agentprobe
echo ".agentprobe" >> .gitignore
```

### Method 3: Environment Variables (Legacy)
If no token file or config file is found, AgentProbe falls back to the SDK's environment variable detection:

1. **OAuth Token** (Primary): `CLAUDE_CODE_OAUTH_TOKEN` environment variable
2. **API Key** (Fallback): `ANTHROPIC_API_KEY` environment variable

**Note**: Using environment variables may affect other Claude CLI processes in the same environment. Token files and config files provide better isolation.

## Key Dependencies

- `claude-code-sdk` - Core integration for running Claude Code programmatically
- `typer` - CLI framework
- `rich` - Terminal formatting and output
- `anyio` - Async runtime for SDK operations

## Tool-Agnostic Design

The codebase intentionally contains no tool-specific logic. All CLI tools (vercel, gh, docker, etc.) are handled generically through the same execution path. Tool-specific behavior should only exist in scenario text files, never in Python code.

## Entry Points

- CLI: `agentprobe.cli:app` (defined in pyproject.toml)
- Python API: `agentprobe.test_cli()` function for programmatic usage

## Important Patterns

- All scenario execution is async (uses Claude Code SDK's async API)
- Results include trace data, success/failure, duration, and cost metrics
- Analysis is pattern-based and should work across all CLI tools
- Community benchmark table in README.md should be updated when adding new tools/scenarios

## Publishing to PyPI

AgentProbe can be published to PyPI to enable users to run `uvx agentprobe` directly without cloning the repository.

### Publishing Process

Always test on TestPyPI first, then publish to PyPI if everything works correctly.

### Token Management with pass

This project uses the `pass` CLI tool for secure token management. Store your PyPI tokens securely:

```bash
# Store TestPyPI token
pass insert pypi/testpypi-token

# Store production PyPI token  
pass insert pypi/production-token

# Verify tokens are stored (will show encrypted tokens)
pass pypi/testpypi-token
pass pypi/production-token
```

**Note**: Both tokens are now configured and ready to use.

#### Step 1: Test on TestPyPI

```bash
# Build the package
uv build

# Publish to TestPyPI using pass
uv publish --publish-url https://test.pypi.org/legacy/ --token $(pass pypi/testpypi-token)

# Test the published package
uvx --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agentprobe --help
```

#### Step 2: Publish to PyPI (Production)

Only proceed if TestPyPI installation and testing is successful:

```bash
# Publish to production PyPI using pass
uv publish --token $(pass pypi/production-token)
```

#### Step 3: Verify Production Installation

```bash
# Test production installation
uvx agentprobe --help
uvx agentprobe benchmark --all
```

### Version Management

Before publishing:
1. Update version in `pyproject.toml`
2. Commit and tag the release
3. Push to GitHub
4. Then publish to PyPI

### TestPyPI vs PyPI

- **TestPyPI**: Use for testing package installation and functionality
- **PyPI**: Production repository for end users
- Always test on TestPyPI first to catch packaging issues

## Development Workflow

- Use conventional commits and after every major change to the source code you should commit it and push it to GitHub.