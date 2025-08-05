# CLI Reference

Complete reference for all AgentProbe commands and options.

## Global Usage

```bash
agentprobe [COMMAND] [OPTIONS] [ARGUMENTS]
```

**Global Options:**
- `--version` - Show version and exit
- `--help` - Show help message

## Commands Overview

| Command | Purpose | Example |
|---------|---------|---------|
| `test` | Run single scenario | `agentprobe test git --scenario status` |
| `benchmark` | Run multiple scenarios | `agentprobe benchmark git` |
| `report` | Generate result reports | `agentprobe report --format json` |
| `community` | View community data | `agentprobe community stats git` |
| `config` | Manage configuration | `agentprobe config get` |

---

## test

Run a single test scenario against a CLI tool.

### Usage

```bash
agentprobe test TOOL --scenario SCENARIO [OPTIONS]
```

### Arguments

- `TOOL` **(required)** - CLI tool to test (e.g., git, docker, vercel)

### Options

- `--scenario`, `-s` **(required)** - Scenario name to run
- `--work-dir`, `-w` - Working directory for the test
- `--max-turns` - Maximum agent interactions (default: 50)
- `--runs` - Number of times to run scenario (default: 1) 
- `--verbose`, `-v` - Show detailed trace of AI conversation
- `--oauth-token-file` - Path to file containing Claude Code OAuth token

### Examples

```bash
# Basic test
agentprobe test git --scenario status

# Test with verbose output
agentprobe test git --scenario status --verbose

# Test in specific directory
agentprobe test git --scenario status --work-dir /path/to/project

# Run scenario multiple times
agentprobe test vercel --scenario deploy --runs 3

# Use custom OAuth token
agentprobe test git --scenario status --oauth-token-file ~/.agentprobe-token
```

### Output

```
╭─────────────────────────── AgentProbe Results ───────────────────────────╮
│ Tool: git | Scenario: status                                             │
│ AX Score: A (2 turns, 60% success rate)                                  │
│                                                                          │
│ Agent Experience Summary:                                                │
│ The agent completed the task perfectly in a single turn...              │
│                                                                          │
│ Duration: 8.2s | Cost: $0.071                                           │
│                                                                          │
│ Use --verbose for full trace analysis                                   │
╰──────────────────────────────────────────────────────────────────────────╯
```

### AX Scores

- **A** - Excellent (90-100% success rate)
- **B** - Good (80-89% success rate)  
- **C** - Average (70-79% success rate)
- **D** - Below Average (60-69% success rate)
- **F** - Failed (0-59% success rate)

---

## benchmark

Run multiple test scenarios, optionally across all tools.

### Usage

```bash
# Benchmark specific tool
agentprobe benchmark TOOL [OPTIONS]

# Benchmark all tools
agentprobe benchmark --all [OPTIONS]
```

### Arguments

- `TOOL` - Tool to benchmark (optional if using --all)

### Options

- `--all` - Run benchmarks for all available tools
- `--oauth-token-file` - Path to file containing Claude Code OAuth token

### Examples

```bash
# Benchmark all git scenarios
agentprobe benchmark git

# Benchmark all tools (long-running!)
agentprobe benchmark --all

# Benchmark with custom token
agentprobe benchmark vercel --oauth-token-file ~/.agentprobe-token
```

### Output

Shows aggregate results across all scenarios:

```
╭─── Benchmark Results: git ───╮
│ Scenarios tested: 3          │
│ Overall AX Score: B          │
│ Average duration: 12.4s      │
│ Total cost: $0.21            │
│                              │
│ Individual results:          │
│ • status: A (8.2s)          │
│ • show-log: B (15.1s)       │
│ • commit-changes: C (14.9s)  │
╰──────────────────────────────╯
```

---

## report

Generate reports from test results in various formats.

### Usage

```bash
agentprobe report [OPTIONS]
```

### Options

- `--format`, `-f` - Output format: `text`, `json`, `markdown` (default: text)
- `--output`, `-o` - Output file path (default: stdout)

### Examples

```bash
# Generate text report
agentprobe report

# Generate JSON report
agentprobe report --format json

# Save markdown report to file
agentprobe report --format markdown --output results.md

# Save JSON report to file
agentprobe report --format json --output results.json
```

### Output Formats

**Text** (default):
```
AgentProbe Test Results
=======================
Tool: git, Scenario: status
Score: A, Duration: 8.2s, Cost: $0.071
...
```

**JSON**:
```json
{
  "results": [
    {
      "tool": "git",
      "scenario": "status", 
      "score": "A",
      "duration": 8.2,
      "cost": 0.071
    }
  ]
}
```

**Markdown**:
```markdown
# AgentProbe Test Results

## git/status
- **Score**: A
- **Duration**: 8.2s  
- **Cost**: $0.071
```

---

## community

View and manage community results and statistics.

### Subcommands

- `stats` - View community statistics
- `show` - Show recent community results

### community stats

View community statistics for tools.

#### Usage

```bash
# All tools leaderboard
agentprobe community stats

# Specific tool stats  
agentprobe community stats TOOL
```

#### Examples

```bash
# View overall leaderboard
agentprobe community stats

# View git-specific stats
agentprobe community stats git

# View vercel-specific stats
agentprobe community stats vercel
```

#### Output

```
🏆 Community Tool Leaderboard
┌─────────┬───────────────┬──────────────┬────────────┐
│ Tool    │ Success Rate  │ Avg Duration │ Total Runs │
├─────────┼───────────────┼──────────────┼────────────┤
│ git     │ 94%          │ 8.2s         │ 1,247      │
│ docker  │ 87%          │ 15.4s        │ 832        │
│ vercel  │ 79%          │ 45.7s        │ 1,891      │
└─────────┴───────────────┴──────────────┴────────────┘
```

### community show

Show recent community results for a specific scenario.

#### Usage

```bash
agentprobe community show TOOL SCENARIO [OPTIONS]
```

#### Arguments

- `TOOL` **(required)** - Tool name
- `SCENARIO` **(required)** - Scenario name

#### Options

- `--last` - Number of recent results to show (default: 10)

#### Examples

```bash
# Show recent git status results
agentprobe community show git status

# Show last 20 vercel deploy results
agentprobe community show vercel deploy --last 20
```

#### Output

```
📊 Recent community results for git/status (last 10)
┌────────────┬───────┬──────────┬─────────┐
│ Timestamp  │ Score │ Duration │ Turns   │
├────────────┼───────┼──────────┼─────────┤
│ 2024-01-20 │ A     │ 7.8s     │ 2       │
│ 2024-01-20 │ A     │ 8.1s     │ 2       │
│ 2024-01-19 │ B     │ 12.4s    │ 3       │
└────────────┴───────┴──────────┴─────────┘
```

---

## config

Manage AgentProbe configuration settings.

### Subcommands

- `set` - Set configuration values
- `get` - Get configuration values

### config set

Set a configuration value.

#### Usage

```bash
agentprobe config set KEY VALUE
```

#### Arguments

- `KEY` **(required)** - Configuration key
- `VALUE` **(required)** - Configuration value

#### Configuration Keys

| Key | Purpose | Values |
|-----|---------|--------|
| `sharing.opted_out` | Control community sharing | `true`, `false` |
| `sharing.api_key` | Custom API key | Any valid API key |
| `sharing.api_url` | Custom API URL | Any valid URL |

#### Examples

```bash
# Opt out of community sharing  
agentprobe config set sharing.opted_out true

# Set custom API key
agentprobe config set sharing.api_key "your-api-key"

# Set custom API URL (for private deployments)
agentprobe config set sharing.api_url "https://your-api.example.com/v1"

# Re-enable sharing
agentprobe config set sharing.opted_out false
```

### config get

Get configuration values.

#### Usage

```bash
# Get all configuration
agentprobe config get

# Get specific key
agentprobe config get KEY
```

#### Examples

```bash
# Show all configuration
agentprobe config get

# Get sharing status
agentprobe config get sharing.opted_out

# Get API URL
agentprobe config get sharing.api_url
```

#### Output

```
Current configuration:
  sharing.enabled: True (enabled)
  sharing.opted_out: False
  sharing.consent_given: True
  sharing.api_url: 
  sharing.api_key: embedded key
  sharing.anonymous_id: 950c455afa7532a5
```

---

## Exit Codes

AgentProbe uses standard exit codes:

- `0` - Success
- `1` - General error 
- `2` - Misuse of shell builtins
- `3` - Configuration error
- `4` - Authentication error

---

## Environment Variables

AgentProbe respects these environment variables:

- `CLAUDE_CODE_OAUTH_TOKEN` - Claude Code OAuth token (recommended)
- `ANTHROPIC_API_KEY` - Anthropic API key (fallback)

---

## Available Tools

Current tools with scenarios:

- **git** - Git version control (status, show-log, commit-changes)
- **docker** - Docker containers (run-nginx)  
- **gh** - GitHub CLI (create-pr)
- **vercel** - Vercel deployments (deploy, init-project, build-local, etc.)
- **netlify** - Netlify deployments (full-lifecycle, function-lifecycle, etc.)
- **wrangler** - Cloudflare Workers (deploy, dev, init, etc.)

See [Scenarios Guide](SCENARIOS.md) for complete list and details.

---

## Tips

- **Start simple**: Use `test git --scenario status` to verify setup
- **Use verbose**: Add `-v` to see the full AI conversation
- **Multiple runs**: Use `--runs N` to test consistency
- **Benchmarks**: Use `benchmark` to test multiple scenarios at once
- **Community data**: Your results help improve CLI tools for everyone