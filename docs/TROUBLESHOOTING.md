# Troubleshooting

Quick solutions for common AgentProbe issues. Listed by problem category with actionable fixes.

## Installation Issues

### "Command not found: agentprobe"

**Problem**: AgentProbe isn't installed or not in PATH.

**Solutions**:
```bash
# Option 1: Use uvx (no installation needed)
uvx agentprobe test git --scenario status

# Option 2: Install with pip
pip install agentprobe

# Option 3: Install with uv
uv pip install agentprobe

# Check if installed
which agentprobe
agentprobe --version
```

### "Package not found" during installation

**Problem**: PyPI package isn't available or network issues.

**Solutions**:
```bash
# Update pip first
pip install --upgrade pip

# Try with verbose output
pip install -v agentprobe

# Use different index
pip install -i https://pypi.org/simple/ agentprobe

# Clear pip cache
pip cache purge
pip install agentprobe
```

## Authentication Issues

### "Authentication failed" or "Invalid API key"

**Problem**: Claude API credentials not set up correctly.

**Solutions**:
```bash
# Check current authentication
echo $CLAUDE_CODE_OAUTH_TOKEN
echo $ANTHROPIC_API_KEY

# Set OAuth token (recommended)
export CLAUDE_CODE_OAUTH_TOKEN="your-token-here"

# Or set API key (fallback)
export ANTHROPIC_API_KEY="your-api-key-here"

# Test authentication
agentprobe test git --scenario status
```

### "Request failed with status 401"

**Problem**: Token/API key is invalid or expired.

**Solutions**:
1. **Get new token**: Visit [Claude Console](https://console.anthropic.com)
2. **Check token format**: Should start with `sk-ant-` (API key) or be a longer OAuth token
3. **Verify in environment**:
   ```bash
   env | grep CLAUDE
   env | grep ANTHROPIC
   ```

### "OAuth token file not found"

**Problem**: Using `--oauth-token-file` with invalid path.

**Solutions**:
```bash
# Check file exists
ls -la ~/.agentprobe-token

# Create token file
echo "your-oauth-token" > ~/.agentprobe-token

# Use absolute path
agentprobe test git --scenario status --oauth-token-file /full/path/to/token

# Or use environment variable instead
export CLAUDE_CODE_OAUTH_TOKEN="your-token"
agentprobe test git --scenario status
```

## Scenario Issues

### "Scenario 'xyz' not found for tool 'abc'"

**Problem**: Scenario doesn't exist or typo in name.

**Solutions**:
```bash
# List available scenarios
ls src/agentprobe/scenarios/git/
find . -name "*.txt" -path "*/scenarios/*"

# Check exact name (no .txt extension needed)
agentprobe test git --scenario status  # ✅ Correct
agentprobe test git --scenario status.txt  # ❌ Wrong

# Check available tools
ls src/agentprobe/scenarios/
```

### AI produces unexpected results

**Problem**: Scenario is unclear or AI misunderstands task.

**Solutions**:
```bash
# Use verbose to see AI conversation
agentprobe test git --scenario status --verbose

# Run multiple times to check consistency
agentprobe test git --scenario status --runs 3

# Try different scenario
agentprobe test git --scenario show-log
```

### "Command not found" during scenario execution

**Problem**: Required CLI tool not installed.

**Solutions**:
```bash
# Install missing tool
# For git:
sudo apt install git  # Ubuntu/Debian
brew install git      # macOS

# For docker:
# Follow Docker installation guide

# For vercel:
npm install -g vercel

# For netlify:
npm install -g netlify-cli

# For gh (GitHub CLI):
brew install gh       # macOS
sudo apt install gh  # Ubuntu

# Verify installation
git --version
docker --version
vercel --version
```

## Network and Connectivity

### "Connection timeout" or "Network error"

**Problem**: Network connectivity issues to Claude API.

**Solutions**:
```bash
# Test internet connectivity
ping google.com

# Test Claude API connectivity
curl -I https://api.anthropic.com

# Check proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY

# Bypass proxy temporarily
unset HTTP_PROXY HTTPS_PROXY
agentprobe test git --scenario status
```

### "SSL certificate verification failed"

**Problem**: SSL/TLS certificate issues.

**Solutions**:
```bash
# Update certificates (macOS)
/Applications/Python\ 3.x/Install\ Certificates.command

# Update certificates (Ubuntu/Debian)
sudo apt-get update && sudo apt-get install ca-certificates

# Check system time (wrong time causes SSL issues)
date

# Temporary workaround (not recommended for production)
export PYTHONHTTPSVERIFY=0
```

## Community Sharing Issues

### "Failed to share result: 401"

**Problem**: Community API authentication failed.

**Solutions**:
```bash
# Check sharing configuration
agentprobe config get

# For local development, set up valid local API key
agentprobe config set sharing.api_key "your-local-dev-key"

# For production, clear custom keys to use embedded key
agentprobe config set sharing.api_key ""

# Opt out of sharing if needed
agentprobe config set sharing.opted_out true
```

### "Request URL is missing protocol"

**Problem**: Invalid API URL configuration.

**Solutions**:
```bash
# Clear invalid URL
agentprobe config set sharing.api_url ""

# Check configuration
agentprobe config get

# Test without sharing
agentprobe config set sharing.opted_out true
agentprobe test git --scenario status
```

### Community data not showing

**Problem**: No community comparison after test.

**Solutions**:
```bash
# Check if sharing is enabled
agentprobe config get sharing.opted_out

# Enable sharing
agentprobe config set sharing.opted_out false

# Check network connectivity to community API
curl -I https://agentprobe-community-production.nikola-balic.workers.dev

# Test community commands directly
agentprobe community stats
```

## Performance Issues

### Tests taking too long

**Problem**: Scenarios timing out or running slowly.

**Solutions**:
```bash
# Reduce max turns for faster execution
agentprobe test git --scenario status --max-turns 10

# Check if tool is responding slowly
git status  # Run tool directly to check performance

# Use simpler scenarios first
agentprobe test git --scenario status  # Simple
# Instead of complex scenarios like:
agentprobe test netlify --scenario full-lifecycle  # Complex
```

### High API costs

**Problem**: Tests consuming too many Claude API credits.

**Solutions**:
```bash
# Use fewer runs
agentprobe test git --scenario status --runs 1  # Instead of multiple runs

# Avoid benchmark --all
agentprobe benchmark git  # Single tool
# Instead of:
agentprobe benchmark --all  # All tools (expensive!)

# Check costs in output
# Look for "Cost: $X.XX" in results
```

## Development and Local Setup

### "Development mode not detected"

**Problem**: Running from source but using production settings.

**Check development mode detection**:
```bash
# Should show development vs production mode
python -c "
from src.agentprobe.submission import _is_development_mode
print(f'Development mode: {_is_development_mode()}')
"
```

**Solutions**:
- Ensure you're running from source directory with `.git` folder
- Use `uv run agentprobe` instead of installed version
- Check directory structure matches `src/agentprobe`

### Local API server not working

**Problem**: Local development server rejecting requests.

**Solutions**:
```bash
# Check if local server is running
curl http://localhost:8787/health

# Check API key format (should use X-API-Key header)
curl -H "X-API-Key: your-key" http://localhost:8787/api/v1/results

# Set up proper local development key
agentprobe config set sharing.api_key "your-valid-local-key"
```

## Common Error Messages

### ImportError: No module named 'agentprobe'

**Solutions**:
```bash
# Reinstall package
pip uninstall agentprobe
pip install agentprobe

# Or use uvx (no installation needed)
uvx agentprobe test git --scenario status
```

### "KeyError: 'trace'" or similar data errors

**Solutions**:
```bash
# Clear any cached data
rm -rf ~/.agentprobe/cache/

# Try a simple scenario first
agentprobe test git --scenario status

# Check if specific to one tool/scenario
agentprobe test docker --scenario run-nginx
```

### "FileNotFoundError" for scenarios

**Solutions**:
```bash
# Verify you're in correct directory
pwd
ls src/agentprobe/scenarios/

# Use full path if needed
agentprobe test git --scenario status --work-dir /full/path/to/project
```

## Diagnostic Commands

### Check System Status

```bash
# AgentProbe version and help
agentprobe --version
agentprobe --help

# Python and dependencies
python --version
pip list | grep agentprobe

# Environment variables
env | grep CLAUDE
env | grep ANTHROPIC

# Configuration
agentprobe config get
```

### Test Basic Functionality

```bash
# Simple test that should always work
agentprobe test git --scenario status --verbose

# Test without community sharing
agentprobe config set sharing.opted_out true
agentprobe test git --scenario status

# Test authentication
agentprobe community stats
```

### Debug Network Issues

```bash
# Test API connectivity
curl -I https://api.anthropic.com
curl -I https://agentprobe-community-production.nikola-balic.workers.dev

# Check DNS resolution
nslookup api.anthropic.com

# Test with verbose HTTP
export PYTHONHTTPSVERIFY=0
python -c "
import requests
response = requests.get('https://api.anthropic.com')
print(response.status_code)
"
```

## Getting More Help

### Enable Verbose Output

Always use `--verbose` when troubleshooting:
```bash
agentprobe test git --scenario status --verbose
```

This shows the full AI conversation and helps identify where things go wrong.

### Collect System Information

```bash
# Create a system info report
echo "=== System Info ===" > debug.txt
uname -a >> debug.txt
python --version >> debug.txt
agentprobe --version >> debug.txt
echo "=== Environment ===" >> debug.txt
env | grep -E "(CLAUDE|ANTHROPIC)" >> debug.txt
echo "=== Configuration ===" >> debug.txt
agentprobe config get >> debug.txt
```

### Reset to Clean State

```bash
# Clear all configuration
rm -f ~/.agentprobe/sharing.json

# Clear any caches
rm -rf ~/.agentprobe/cache/

# Reinstall package
pip uninstall agentprobe
pip install agentprobe

# Test basic functionality
agentprobe test git --scenario status
```

---

**Still having issues?**

1. Check [GitHub Issues](https://github.com/nibzard/agentprobe/issues) for similar problems
2. Create a new issue with:
   - Error message (full text)
   - Command you ran
   - System info (OS, Python version)
   - Verbose output (`--verbose`)

**Quick win**: Most issues are solved by ensuring proper authentication setup and using simple scenarios first! 🚀