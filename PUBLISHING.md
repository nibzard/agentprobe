# Publishing to PyPI

This document provides step-by-step instructions for publishing AgentProbe to PyPI, based on lessons learned from actual publishing experience, including the major v0.2.0 community-first architecture release and v0.2.1 patch with --version flag.

## Prerequisites

1. **Token Management**: Ensure you have PyPI tokens stored securely using `pass`:
   ```bash
   # Store TestPyPI token
   pass insert pypi/testpypi-token
   
   # Store production PyPI token  
   pass insert pypi/production-token
   ```

2. **Version Synchronization**: Always keep versions synchronized across files:
   - `pyproject.toml` - Primary version source
   - `src/agentprobe/__init__.py` - Used by CLI --version flag
   
3. **Git State**: Ensure all changes are committed before publishing to maintain clean release history.

## Publishing Process

### Step 1: Prepare Release

1. **Check Current Versions**:
   ```bash
   # Check pyproject.toml version
   grep "version =" pyproject.toml
   
   # Check __init__.py version
   grep "__version__" src/agentprobe/__init__.py
   ```

2. **Update Versions Consistently**:
   ```bash
   # Update pyproject.toml
   # version = "0.2.x"  # Increment as needed
   
   # Update __init__.py to match
   # __version__ = "0.2.x"
   ```

3. **Test Version Display**:
   ```bash
   uv run agentprobe --version
   # Should output: agentprobe 0.2.x
   ```

### Step 2: Commit and Tag Release

1. **Commit All Changes**:
   ```bash
   git add .
   git commit -m "feat: add new feature / fix: bug description
   
   🤖 Generated with [Claude Code](https://claude.ai/code)
   
   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

2. **Tag the Release**:
   ```bash
   git tag v0.2.x
   git push origin main --tags
   ```

### Step 3: Clean and Build

1. **Clean Previous Builds** (CRITICAL - prevents publishing old versions):
   ```bash
   rm -rf dist/
   ```

2. **Build the Package**:
   ```bash
   uv build
   ```

   This should create:
   - `dist/agentprobe-0.2.x.tar.gz` (source distribution)
   - `dist/agentprobe-0.2.x-py3-none-any.whl` (wheel)

### Step 4: Test on TestPyPI First

1. **Publish to TestPyPI**:
   ```bash
   uv publish --publish-url https://test.pypi.org/legacy/ --token $(pass pypi/testpypi-token)
   ```

2. **Test Installation and Basic Functionality**:
   ```bash
   # Test help
   uvx --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agentprobe --help
   
   # Test version flag
   uvx --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agentprobe --version
   
   # Test community features (if applicable)
   uvx --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agentprobe community stats
   ```

3. **Verify Critical Features Work**:
   - CLI commands load properly
   - Version displays correctly
   - Community features (if using embedded API keys) connect successfully
   - No import errors or missing dependencies

### Step 5: Publish to Production PyPI

1. **Only Proceed if TestPyPI Was Successful** ⚠️

2. **Publish to Production**:
   ```bash
   uv publish --token $(pass pypi/production-token)
   ```

### Step 6: Verify Production Installation

⏰ **Note**: PyPI propagation can take 5-15 minutes. Be patient.

1. **Test Specific Version** (recommended):
   ```bash
   # Test specific version to ensure you get the new release
   uvx agentprobe@0.2.x --version
   uvx agentprobe@0.2.x --help
   ```

2. **Test Latest Version**:
   ```bash
   # May take time to propagate
   uvx agentprobe --version
   uvx agentprobe --help
   ```

3. **Test Community Features** (for versions with embedded keys):
   ```bash
   # Clear local config for fresh test
   rm -f ~/.agentprobe/sharing.json
   
   # Test consent flow and community sharing
   echo "y" | uvx agentprobe@0.2.x test git --scenario status
   
   # Test community stats
   uvx agentprobe@0.2.x community stats
   ```

## Common Issues and Solutions

### Issue: "File already exists" Error

**Problem**: Trying to publish a version that already exists on PyPI.

**Solution**: 
1. Update version in BOTH `pyproject.toml` AND `src/agentprobe/__init__.py`
2. Clean the `dist/` directory: `rm -rf dist/`
3. Rebuild: `uv build`
4. Retry publishing

### Issue: Publishing Old Versions

**Problem**: `uv publish` uploads ALL files in `dist/`, including old versions.

**Solution**: Always clean the `dist/` directory before building:
```bash
rm -rf dist/ && uv build
```

### Issue: Version Mismatch

**Problem**: CLI shows different version than expected (e.g., `agentprobe --version` shows old version).

**Solution**: Ensure version synchronization:
```bash
# Check both files match
grep "version =" pyproject.toml
grep "__version__" src/agentprobe/__init__.py

# Update both to match, then rebuild
```

### Issue: Community Features Not Working

**Problem**: Embedded API keys don't work or community features fail.

**Solution**: 
1. Verify embedded key is properly obfuscated in `submission.py`
2. Test with explicit version: `uvx agentprobe@0.2.x community stats`
3. Check API endpoint is accessible
4. Clear local config: `rm -f ~/.agentprobe/sharing.json`

### Issue: PyPI Propagation Delays

**Problem**: New version not available immediately after publishing.

**Solution**: 
- Wait 5-15 minutes for PyPI to propagate
- Use specific version syntax: `uvx agentprobe@0.2.x`
- Avoid `--force-reinstall` with uvx (doesn't work)
- Check PyPI web interface to confirm upload

## Best Practices

1. **Always test on TestPyPI first** - This catches packaging issues before they affect production users.

2. **Clean builds** - Always remove the `dist/` directory before building to avoid publishing old versions.

3. **Version Synchronization** - Keep `pyproject.toml` and `__init__.py` versions in sync for CLI --version flag.

4. **Git Workflow** - Commit, tag, and push before publishing for clean release history.

5. **Security** - Use `pass` or another secure method to store PyPI tokens instead of environment variables.

6. **Verification** - Always verify the published package works by installing specific version with `uvx package@version`.

7. **Community Features** - Test embedded API keys and community functionality after publishing.

8. **Patience with PyPI** - Allow 5-15 minutes for new releases to propagate before expecting availability.

## Version Increment Strategy

- **Patch version** (0.2.x): Bug fixes, small improvements (e.g., adding --version flag)
- **Minor version** (0.x.0): New features, backwards compatible (e.g., community sharing system)
- **Major version** (x.0.0): Breaking changes, API changes

### Real Examples:
- **v0.2.0**: Major community-first architecture with embedded API keys, consent flow, auto-sharing
- **v0.2.1**: Added --version flag (patch - small improvement)

## Release Types and Commit Messages

### Feature Releases (Minor versions)
```bash
git commit -m "feat: implement community-first architecture with automatic data sharing

- Add embedded API key system with obfuscation for zero-setup experience
- Implement first-run consent dialog with clear privacy messaging
- Remove --share flag requirement - all tests now contribute automatically

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Patch Releases
```bash
git commit -m "feat: add --version flag to CLI

- Add version callback function to display version info
- Support both --version and -v flags
- Update __init__.py version to match pyproject.toml

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

## Troubleshooting

### Publishing Failures
1. **Check token storage**: `pass pypi/production-token` should return valid token
2. **Version conflicts**: Ensure version doesn't exist on PyPI
3. **Clean dist**: `rm -rf dist/` before building
4. **Dependencies**: Verify all `pyproject.toml` dependencies exist on PyPI
5. **Network issues**: Check PyPI status page

### Post-Publishing Issues
1. **Package not available**: Wait 5-15 minutes for propagation
2. **Wrong version installed**: Use `uvx package@specific-version`
3. **Import errors**: Check dependencies and test on TestPyPI first
4. **Community features failing**: Verify embedded API keys and network connectivity

### Token Management
- Regenerate tokens on PyPI/TestPyPI web interface if auth fails
- Update in `pass`: `pass edit pypi/production-token`
- Test token: `curl -H "Authorization: Bearer $(pass pypi/production-token)" https://pypi.org/simple/`

### Quick Debug Checklist
```bash
# Version sync check
grep "version =" pyproject.toml && grep "__version__" src/agentprobe/__init__.py

# Clean build
rm -rf dist/ && uv build

# Test local version
uv run agentprobe --version

# Check PyPI upload
ls -la dist/  # Should only show current version files
```