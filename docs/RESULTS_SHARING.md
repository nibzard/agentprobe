# AgentProbe Results Sharing

This document describes the community results sharing feature for AgentProbe, which allows users to contribute their test results to a shared database for collective insights.

## Overview

The results sharing feature enables:
- 📊 Anonymous submission of test results
- 🌍 Community-wide statistics and trends
- 📈 Success rate tracking across tools and versions
- 🔍 Common friction point identification
- 🏆 Tool leaderboards

## Client-Side Features

### Sharing Results

Share results when running tests:

```bash
# Share a single test result
agentprobe test vercel --scenario deploy --share

# Share all benchmark results
agentprobe benchmark --all --share
```

### Configuration

Configure sharing preferences:

```bash
# Enable sharing by default
agentprobe config set sharing.enabled true

# Set API key (if required)
agentprobe config set sharing.api_key "your-api-key"

# View current configuration
agentprobe config get
```

### Community Commands

View community statistics:

```bash
# View stats for a specific tool
agentprobe community stats vercel

# View recent results for a scenario
agentprobe community show vercel deploy --last 20
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
- Results are aggregated for privacy

### Opt-in by Default

- Sharing is disabled by default
- Users must explicitly enable via `--share` flag or configuration
- Full control over what data is shared

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

## Backend API

The community API provides endpoints for:

### Submission
- `POST /api/v1/results` - Submit test results

### Querying
- `GET /api/v1/results` - Query results with filters
- `GET /api/v1/stats/tool/{tool}` - Tool-specific statistics
- `GET /api/v1/stats/scenario/{tool}/{scenario}` - Scenario statistics
- `GET /api/v1/leaderboard` - Success rate rankings

## Example Backend Implementation

See `examples/backend_api_example.py` for a reference FastAPI implementation.

## Frontend Dashboard

A web dashboard displays:
- Real-time success rates
- Tool performance trends
- Common friction points
- Community leaderboard

See `examples/frontend_example.html` for a reference implementation.

## Development

### Running the Example Backend

```bash
# Install FastAPI
pip install fastapi uvicorn

# Run the example API
python examples/backend_api_example.py
```

### Testing Submission

```bash
# Test with mock API
export AGENTPROBE_API_URL="http://localhost:8000/api/v1"
agentprobe test vercel --scenario deploy --share
```

## Future Enhancements

- 📊 Advanced analytics and insights
- 🔄 Real-time updates via WebSocket
- 📱 Mobile app for monitoring
- 🤖 ML-based pattern detection
- 🏗️ Tool-specific recommendations
- 🌐 Global deployment with CDN

## Contributing

We welcome contributions to improve the results sharing feature! Please ensure:
- Privacy is maintained
- Data sanitization is thorough
- Tests cover new functionality
- Documentation is updated