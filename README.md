# AgentProbe

Test how well AI agents interact with your CLI tools. AgentProbe runs Claude Code against any command-line tool and tells you where it struggles.

## Quick Start

```bash
# No installation needed - just run with uvx
uvx agentprobe test vercel --scenario deploy

# Or install locally
pip install agentprobe
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

## Usage

Test any CLI tool by creating a simple text file with a prompt:

```bash
# Create a scenario
echo "Deploy this app to production" > scenarios/vercel/deploy.txt

# Run the test
agentprobe test vercel --scenario deploy
```

## Example Output

```
╭─ AgentProbe Results ─────────────────────────────────────╮
│ Tool: vercel | Scenario: deploy                         │
│ Status: ✓ SUCCESS | Duration: 23.4s | Cost: $0.012     │
├──────────────────────────────────────────────────────────┤
│ Summary:                                                 │
│ • Successfully deployed to https://app-xi.vercel.app     │
│ • Agent needed 2 attempts to find correct deploy flag   │
│ • Consider adding examples to your --help output        │
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
agentprobe benchmark vercel

# Test all tools
agentprobe benchmark --all

# Generate report
agentprobe report --format markdown > scenarios/RESULTS.md
```

## Requirements

- Python 3.10+
- Claude Code CLI: `npm install -g @anthropic-ai/claude-code`

## Popular Scenarios

Browse our growing collection of test scenarios:

- **Deployment Tools**: vercel, netlify, heroku, fly.io
- **Package Managers**: npm, yarn, pip, cargo
- **Cloud CLIs**: aws, gcloud, azure
- **Dev Tools**: git, gh, docker, kubectl
- **Databases**: psql, mysql, redis-cli

[Browse all scenarios →](scenarios/)

## License

MIT