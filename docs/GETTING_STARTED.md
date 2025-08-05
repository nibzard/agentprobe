# Getting Started with AgentProbe

Get up and running with AgentProbe in under 2 minutes.

## Quick Install

**Recommended**: Use `uvx` for instant access without installation:

```bash
uvx agentprobe test git --scenario status
```

**Alternative methods**:

```bash
# Install globally with pip
pip install agentprobe
agentprobe test git --scenario status

# Install with uv (for development)
uv pip install agentprobe
agentprobe test git --scenario status
```

## Your First Test

Run your first test to see how AI agents handle basic git operations:

```bash
uvx agentprobe test git --scenario status
```

**What happens:**
1. AgentProbe loads the git status scenario
2. Claude analyzes your repository using git commands
3. You get results showing how well the AI performed

## Understanding Your Results

```
╭─────────────────────────── AgentProbe Results ───────────────────────────╮
│ Tool: git | Scenario: status                                             │
│ AX Score: A (2 turns, 60% success rate)                                  │
│                                                                          │
│ Agent Experience Summary:                                                │
│ The agent completed the task perfectly in a single turn using git       │
│ status, which provided all required information clearly.                 │
│                                                                          │
│ Duration: 8.2s | Cost: $0.071                                           │
│                                                                          │
│ Use --verbose for full trace analysis                                   │
╰──────────────────────────────────────────────────────────────────────────╯
```

**Key metrics:**
- **AX Score**: A-F grade (A = excellent, F = failed)
- **Turns**: How many back-and-forth interactions needed
- **Duration**: How long the task took
- **Cost**: API cost for the Claude calls

## Community Comparison

After your test, see how you compare to the community:

```
🌍 Community Comparison for git/status:
✅ Success (matches community average)
⏱️  Duration: 8.2s vs 7.8s avg (average speed)
📊 Based on 13 community runs
```

## Try More Scenarios

**Easy scenarios** (great for learning):
```bash
# Git operations
uvx agentprobe test git --scenario show-log

# Docker basics  
uvx agentprobe test docker --scenario run-nginx

# GitHub operations
uvx agentprobe test gh --scenario create-pr
```

**Advanced scenarios** (test complex workflows):
```bash
# Vercel deployment
uvx agentprobe test vercel --scenario deploy

# Netlify full lifecycle
uvx agentprobe test netlify --scenario full-lifecycle

# Cloudflare Workers
uvx agentprobe test wrangler --scenario deploy
```

## Running Multiple Tests

Test multiple scenarios at once:

```bash
# Benchmark all git scenarios
uvx agentprobe benchmark git

# Benchmark everything (warning: takes time!)
uvx agentprobe benchmark --all
```

## Authentication Setup

AgentProbe needs Claude API access. Set up authentication:

```bash
# Method 1: OAuth token (recommended)
export CLAUDE_CODE_OAUTH_TOKEN="your-token-here"

# Method 2: API key (fallback)
export ANTHROPIC_API_KEY="your-api-key-here"
```

**Get your tokens:**
- OAuth token: [Claude Console](https://console.anthropic.com)
- API key: [Anthropic API](https://console.anthropic.com/api-keys)

## First Run Consent

On first use, AgentProbe asks for consent to share anonymous results:

```
🤖 Welcome to AgentProbe!

AgentProbe collects anonymous usage data to improve CLI tools for AI agents.

✓ Data is anonymized and sanitized
✓ No personal information is collected  
✓ You can opt out anytime

Share anonymous data to help improve CLI tools? [Y/n]:
```

**Safe to say yes** - helps improve CLI tools for everyone.

## What's Next?

1. **Explore available scenarios**: See [Scenarios Guide](SCENARIOS.md)
2. **Learn all commands**: Check [CLI Reference](CLI_REFERENCE.md)  
3. **Having issues?**: Visit [Troubleshooting](TROUBLESHOOTING.md)
4. **Want to contribute?**: Read [Development Guide](DEVELOPMENT.md)

## Quick Tips

- **Start simple**: Use `git --scenario status` to verify everything works
- **Use verbose**: Add `--verbose` to see full AI conversation
- **Check community**: Your results help identify tool usability issues
- **Try benchmarks**: Use `benchmark` command to test multiple scenarios

## Need Help?

```bash
# Get help for any command
uvx agentprobe --help
uvx agentprobe test --help
uvx agentprobe benchmark --help

# Check your configuration
uvx agentprobe config get
```

---

**Ready to test how AI agents interact with your favorite CLI tools?** Start with `uvx agentprobe test git --scenario status` and explore from there! 🚀