# Publishing to PyPI

This document provides step-by-step instructions for publishing AgentProbe to PyPI, based on lessons learned from actual publishing experience.

## Prerequisites

1. **Token Management**: Ensure you have PyPI tokens stored securely using `pass`:
   ```bash
   # Store TestPyPI token
   pass insert pypi/testpypi-token
   
   # Store production PyPI token  
   pass insert pypi/production-token
   ```

2. **Version Management**: Always increment the version in `pyproject.toml` before publishing to avoid conflicts with existing packages.

## Publishing Process

### Step 1: Check and Update Version

1. Check the current version in `pyproject.toml`:
   ```bash
   grep "version =" pyproject.toml
   ```

2. If needed, update the version number to avoid conflicts:
   ```toml
   version = "0.1.x"  # Increment as needed
   ```

### Step 2: Clean and Build

1. Clean any existing builds to avoid publishing old versions:
   ```bash
   rm -rf dist/
   ```

2. Build the package:
   ```bash
   uv build
   ```

   This should create:
   - `dist/agentprobe-x.x.x.tar.gz` (source distribution)
   - `dist/agentprobe-x.x.x-py3-none-any.whl` (wheel)

### Step 3: Test on TestPyPI First

1. Publish to TestPyPI:
   ```bash
   uv publish --publish-url https://test.pypi.org/legacy/ --token $(pass pypi/testpypi-token)
   ```

2. Test the TestPyPI installation:
   ```bash
   uvx --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agentprobe --help
   ```

3. Verify the command works and displays the expected help output.

### Step 4: Publish to Production PyPI

1. Only proceed if TestPyPI testing was successful.

2. Publish to production PyPI:
   ```bash
   uv publish --token $(pass pypi/production-token)
   ```

### Step 5: Verify Production Installation

1. Test production installation:
   ```bash
   uvx agentprobe --help
   ```

2. Run a quick benchmark to ensure everything works:
   ```bash
   uvx agentprobe benchmark --all --oauth-token-file ~/.agentprobe-token
   ```

## Common Issues and Solutions

### Issue: "File already exists" Error

**Problem**: Trying to publish a version that already exists on PyPI.

**Solution**: 
1. Update the version number in `pyproject.toml`
2. Clean the `dist/` directory: `rm -rf dist/`
3. Rebuild: `uv build`
4. Retry publishing

### Issue: Publishing Old Versions

**Problem**: `uv publish` tries to upload all files in `dist/`, including old versions.

**Solution**: Always clean the `dist/` directory before building:
```bash
rm -rf dist/ && uv build
```

### Issue: TestPyPI vs PyPI Differences

**Problem**: Package works on TestPyPI but fails on PyPI due to dependency differences.

**Solution**: Always test the full installation process on TestPyPI first, including running actual commands, not just `--help`.

## Best Practices

1. **Always test on TestPyPI first** - This catches packaging issues before they affect production users.

2. **Clean builds** - Always remove the `dist/` directory before building to avoid publishing old versions.

3. **Version management** - Check if the version already exists on PyPI before attempting to publish.

4. **Security** - Use `pass` or another secure method to store PyPI tokens instead of environment variables.

5. **Verification** - Always verify the published package actually works by installing it fresh with `uvx`.

## Version Increment Strategy

- **Patch version** (0.1.x): Bug fixes, small improvements
- **Minor version** (0.x.0): New features, backwards compatible
- **Major version** (x.0.0): Breaking changes

For this project, increment patch versions for most releases unless adding significant new features or making breaking changes.

## Post-Publishing Steps

1. **Commit version change**:
   ```bash
   git add pyproject.toml
   git commit -m "chore: bump version to x.x.x for PyPI release"
   ```

2. **Tag the release**:
   ```bash
   git tag v0.1.x
   git push origin main --tags
   ```

3. **Update README or CHANGELOG** if needed to reflect the new version.

## Troubleshooting

If publishing fails:
1. Check that tokens are correctly stored in `pass`
2. Verify the version doesn't already exist on PyPI
3. Ensure the `dist/` directory only contains the current version
4. Check that all dependencies in `pyproject.toml` are available on PyPI

For token issues, regenerate tokens on PyPI/TestPyPI and update them in `pass`.