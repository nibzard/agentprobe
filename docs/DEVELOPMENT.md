# Development Guide

How to contribute to AgentProbe, set up development environment, and add new features.

## Quick Start for Contributors

### 1. Get the Code
```bash
# Clone the repository
git clone https://github.com/nibzard/agentprobe.git
cd agentprobe

# Set up development environment
uv sync
```

### 2. Test Your Setup
```bash
# Run AgentProbe from source
uv run agentprobe test git --scenario status

# This should work and show "Development mode: True" internally
```

### 3. Make Your First Contribution
- **Add a scenario**: Easiest way to contribute (see [Scenarios Guide](SCENARIOS.md))
- **Fix documentation**: Improve these docs or add examples
- **Report bugs**: Create issues with detailed reproduction steps

## Development Environment

### Prerequisites
- **Python 3.8+** - Check with `python --version`
- **uv** - Install from [docs.astral.sh/uv](https://docs.astral.sh/uv/)
- **Git** - For version control

### Setup
```bash
# Clone and enter directory
git clone https://github.com/nibzard/agentprobe.git
cd agentprobe

# Install dependencies with development extras
uv sync --extra dev

# Verify setup
uv run agentprobe --version
uv run agentprobe test git --scenario status
```

### Project Structure
```
agentprobe/
├── src/agentprobe/           # Main source code
│   ├── scenarios/            # All test scenarios
│   ├── cli.py               # Command-line interface
│   ├── runner.py            # Scenario execution
│   ├── analyzer.py          # Result analysis
│   └── reporter.py          # Output formatting
├── docs/                    # Documentation
├── tests/                   # Test suite
└── CLAUDE.md               # Detailed dev instructions
```

## Contributing Scenarios

**Easiest way to contribute!** Scenarios are simple text files that describe tasks for AI agents.

### Adding New Scenarios

1. **Choose existing tool** or create new tool directory:
   ```bash
   # For existing tool
   ls src/agentprobe/scenarios/git/

   # For new tool
   mkdir src/agentprobe/scenarios/newtool/
   ```

2. **Create scenario file**:
   ```bash
   # Use descriptive name with hyphens
   touch src/agentprobe/scenarios/git/merge-conflict.txt
   ```

3. **Write clear instructions**:
   ```
   Create two branches that modify the same file in different ways.
   Merge them to create a conflict, then resolve the conflict manually.
   Verify the merge was successful and the file contains both changes.
   ```

4. **Test your scenario**:
   ```bash
   # Test multiple times to ensure consistency
   uv run agentprobe test git --scenario merge-conflict --runs 3

   # Use verbose to see AI interpretation
   uv run agentprobe test git --scenario merge-conflict --verbose
   ```

5. **Submit for review**:
   ```bash
   git add src/agentprobe/scenarios/git/merge-conflict.txt
   git commit -m "feat: add git merge-conflict scenario"
   git push origin feature/merge-conflict-scenario
   ```

### Scenario Writing Guidelines

**✅ Good Scenarios**:
- Clear, specific instructions
- Include context and setup
- Define success criteria
- Work across different environments

**❌ Avoid**:
- Vague instructions ("do something with git")
- Hardcoded values that might not exist
- Assumptions about system state
- Multiple tools in one scenario

See [Scenarios Guide](SCENARIOS.md) for detailed examples.

## Code Contributions

### Development Workflow

1. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and test**:
   ```bash
   # Run tests (when implemented)
   uv run pytest

   # Test your changes
   uv run agentprobe test git --scenario status

   # Format code
   uv run black src/
   uv run ruff check src/
   ```

3. **Commit and push**:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin feature/your-feature-name
   ```

4. **Create pull request**:
   - Clear description of changes
   - Include test results
   - Reference any related issues

### Areas for Contribution

#### 🎯 High Impact, Easy
- **New scenarios**: Add test cases for existing tools
- **Documentation**: Improve examples, fix typos
- **Error messages**: Make them more helpful
- **Output formatting**: Improve result display

#### 🚀 Medium Impact, Medium Difficulty
- **New tool support**: Add entire new CLI tools
- **Analysis improvements**: Better success/failure detection
- **Performance**: Faster execution, better caching
- **Reporting**: JSON/markdown output formats

#### 🔬 High Impact, Hard
- **Architecture**: Core improvements to runner/analyzer
- **Community features**: Enhanced statistics and comparisons
- **AI optimization**: Better prompts, fewer API calls
- **Testing framework**: Comprehensive test suite

### Code Style

AgentProbe follows standard Python conventions:

```bash
# Format code
uv run black src/

# Check linting
uv run ruff check src/

# Type checking (if implemented)
uv run mypy src/
```

**Key principles**:
- Simple, readable code
- Clear variable names
- Comprehensive error handling
- Minimal dependencies

## Testing

### Manual Testing
```bash
# Test basic functionality
uv run agentprobe test git --scenario status

# Test different tools
uv run agentprobe test docker --scenario run-nginx
uv run agentprobe test vercel --scenario deploy

# Test benchmarks
uv run agentprobe benchmark git

# Test community features
uv run agentprobe community stats
```

### Automated Testing
```bash
# Run test suite (when implemented)
uv run pytest

# Test specific module
uv run pytest tests/test_scenarios.py

# With coverage
uv run pytest --cov=agentprobe
```

### Integration Testing
```bash
# Test with different Python versions
uv run --python 3.8 agentprobe test git --scenario status
uv run --python 3.11 agentprobe test git --scenario status

# Test installation from package
pip install -e .
agentprobe test git --scenario status
```

## Local Development with Community Backend

If you're working on community features, you'll need the local backend:

### 1. Set Up Local API Server
See [Results Sharing Guide](RESULTS_SHARING.md#local-development-setup) for detailed instructions.

### 2. Configure AgentProbe
```bash
# AgentProbe automatically detects development mode
# Just set up a valid local API key
uv run agentprobe config set sharing.api_key "your-local-dev-key"
```

### 3. Test Community Features
```bash
# Test result sharing
uv run agentprobe test git --scenario status

# Test community commands
uv run agentprobe community stats
```

## Debugging

### Debug Mode
```bash
# Verbose output shows AI conversation
uv run agentprobe test git --scenario status --verbose

# Multiple runs help identify consistency issues
uv run agentprobe test git --scenario status --runs 5
```

### Common Development Issues

**"Development mode not detected"**:
- Ensure you're in the cloned repository
- Use `uv run agentprobe` (not global install)
- Check `.git` directory exists

**"Scenarios not found"**:
- Verify you're running from project root
- Check scenario files exist in `src/agentprobe/scenarios/`

**"Import errors"**:
- Run `uv sync` to ensure dependencies are installed
- Check you're using the right Python environment

### Profiling and Performance

```bash
# Time execution
time uv run agentprobe test git --scenario status

# Profile Python execution (if needed)
python -m cProfile -o profile.out -m agentprobe.cli test git --scenario status
```

## Release Process

For maintainers publishing new versions:

### 1. Prepare Release
```bash
# Update version in pyproject.toml
# Update CHANGELOG (if exists)
# Run final tests
uv run agentprobe benchmark --all
```

### 2. Build and Test
```bash
# Build package
uv build

# Test on TestPyPI first
uv publish --publish-url https://test.pypi.org/legacy/ --token $TESTPYPI_TOKEN

# Test installation
uvx --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agentprobe test git --scenario status
```

### 3. Publish to PyPI
```bash
# Only if TestPyPI worked perfectly
uv publish --token $PYPI_TOKEN
```

See [PUBLISHING.md](../PUBLISHING.md) for detailed instructions.

## Contributing Guidelines

### Pull Request Process

1. **Fork repository** and create feature branch
2. **Write clear commit messages**: Use conventional commits
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `test:` for test additions
3. **Test thoroughly**: Multiple scenarios, different environments
4. **Update documentation**: If adding features or changing behavior
5. **Request review**: Tag relevant maintainers

### Issue Reporting

When reporting bugs or requesting features:

**Include**:
- AgentProbe version (`agentprobe --version`)
- Python version (`python --version`)
- Operating system
- Full error message
- Steps to reproduce
- Expected vs actual behavior

**Example**:
```
**Bug**: agentprobe test fails with authentication error

**Environment**:
- AgentProbe: 0.2.1
- Python: 3.11.0
- OS: macOS 14.0

**Steps**:
1. Run `agentprobe test git --scenario status`
2. See error: "Authentication failed"

**Expected**: Test should run successfully
**Actual**: Authentication error despite valid token

**Logs**:
```
[error logs here]
```
```

### Code of Conduct

- **Be respectful**: Treat all contributors with respect
- **Be inclusive**: Welcome contributors of all backgrounds
- **Be helpful**: Provide constructive feedback
- **Be patient**: Not everyone has the same experience level

## Community

### Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Start with [Getting Started](GETTING_STARTED.md)

### Staying Updated

- **Watch repository**: Get notifications for releases
- **Follow releases**: Subscribe to new version announcements
- **Join discussions**: Participate in feature planning

---

**Ready to contribute?** Start with adding a simple scenario for your favorite CLI tool. Every contribution, no matter how small, helps make CLI tools more accessible to AI agents! 🚀

**Technical details**: See [CLAUDE.md](../CLAUDE.md) for detailed architecture and implementation information.