# AgentProbe Community Platform

AgentProbe is a community-first platform that automatically collects anonymous usage data to improve CLI tools for AI agents. This document describes how the community sharing system works.

## Overview

The community platform enables:
- 📊 Automatic anonymous submission of test results  
- 🌍 Real-time community statistics and comparisons
- 📈 Success rate tracking across tools and scenarios
- 🔍 Common friction point identification
- 🏆 Tool performance leaderboards
- 🤝 Collective insights to improve CLI usability

## How It Works

### Automatic Community Sharing

AgentProbe automatically shares results with the community:

```bash
# All tests automatically contribute to community data
agentprobe test vercel --scenario deploy

# Benchmarks automatically share all results  
agentprobe benchmark --all

# View community statistics
agentprobe community stats vercel
```

### First-Run Consent

On your first use, AgentProbe will show a consent dialog:

```
🤖 Welcome to AgentProbe!

AgentProbe collects anonymous usage data to improve CLI tools for AI agents.
This helps identify common friction points and success patterns.

✓ Data is anonymized and sanitized
✓ No personal information is collected  
✓ You can opt out anytime

Share anonymous data to help improve CLI tools? [Y/n]:
```

### Community Comparison

After each test, see how your results compare:

```
🌍 Community Comparison for git/status:
✅ Success (matches community average)
⏱️  Duration: 8.7s vs 7.4s avg (average speed)
📊 Based on 15 community runs
```

### Community Commands

Explore community data:

```bash
# View leaderboard of all tools
agentprobe community stats

# View stats for a specific tool  
agentprobe community stats git

# View recent results for a scenario
agentprobe community show git status --last 10
```

## Privacy & Security

### Data Sanitization

All submitted data is automatically sanitized to remove:
- 🔑 API keys, tokens, and secrets
- 📧 Email addresses  
- 🌐 IP addresses
- 📁 Personal file paths
- 🔐 Authentication headers

### Anonymous Submission

- Each client generates a stable anonymous ID
- No personally identifiable information is collected
- Results are aggregated for privacy protection

### Opt-In by Default with Easy Opt-Out

- **Community sharing is enabled by default** after consent
- Clear consent dialog on first use explains data collection
- **Easy opt-out** anytime with full control over your data
- No API keys or account setup required

## Data Model

### Submitted Data Structure

```json
{
  "run_id": "uuid",
  "timestamp": "2024-01-20T10:30:00Z",
  "tool": "vercel",
  "scenario": "deploy",
  "client_info": {
    "agentprobe_version": "0.1.0",
    "os": "linux",
    "python_version": "3.11.0"
  },
  "execution": {
    "duration": 45.2,
    "total_turns": 8,
    "success": true
  },
  "analysis": {
    "friction_points": ["authentication", "unclear_error"],
    "help_usage_count": 2,
    "recommendations": ["Better error messages needed"]
  }
}
```

## Configuration

### Opt-Out of Sharing

You can opt out of community sharing at any time:

```bash
# Opt out of community data sharing
agentprobe config set sharing.opted_out true

# View current sharing status
agentprobe config get

# Re-enable sharing
agentprobe config set sharing.opted_out false
```

### Advanced Configuration

For advanced users, additional configuration options are available:

```bash
# Override API URL (for testing or private deployments)
agentprobe config set sharing.api_url "https://your-api.example.com/v1"

# Override embedded API key (not recommended)  
agentprobe config set sharing.api_key "your-custom-key"
```

## Community API

The AgentProbe community runs on a secure, scalable API:

- **Production**: `https://agentprobe-community-production.nikola-balic.workers.dev`
- **Authentication**: Release-specific embedded keys (no user setup required)
- **Rate Limiting**: By anonymous user ID to prevent abuse
- **Data Retention**: Aggregated statistics with privacy protection

### Available Endpoints

- `GET /api/v1/leaderboard` - Tool performance rankings
- `GET /api/v1/stats/tool/{tool}` - Tool-specific statistics  
- `GET /api/v1/stats/scenario/{tool}/{scenario}` - Scenario statistics
- `POST /api/v1/results` - Submit test results (automatic)

## Benefits for the Community

By participating, you help:

- **🔍 Identify Pain Points**: Find common CLI usability issues
- **📊 Track Improvements**: See how tool updates affect AI agent success  
- **🏆 Compare Tools**: Understand which tools work best for agents
- **🤝 Share Knowledge**: Help other developers choose the right tools
- **🚀 Drive Progress**: Influence CLI tool development with real usage data

## Getting Started

1. **Install AgentProbe**: `uvx agentprobe` or `pip install agentprobe`
2. **Run your first test**: `agentprobe test git --scenario status`
3. **Give consent** when prompted on first run
4. **See community comparison** after your test completes
5. **Explore community data**: `agentprobe community stats`

## Troubleshooting

### Sharing Not Working

```bash
# Check your configuration
agentprobe config get

# Verify you haven't opted out
agentprobe config set sharing.opted_out false

# Test connectivity
agentprobe community stats
```

### Reset Configuration

```bash
# Remove all sharing configuration
rm ~/.agentprobe/sharing.json

# Next run will show consent dialog again
agentprobe test git --scenario status
```

## Contributing

Help improve the AgentProbe community platform:

- **Submit Issues**: Report bugs or request features
- **Share Feedback**: Tell us about your experience
- **Contribute Code**: Improve the CLI or community features  
- **Spread the Word**: Help grow the community

**Privacy First**: All contributions must maintain user privacy and data protection standards.