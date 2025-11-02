# PyPI Publication Checklist

This document outlines the steps to publish GuideRails to PyPI for the first time.

## Prerequisites

All code changes for PyPI packaging have been completed:
- ✅ Build backend migrated to hatchling
- ✅ Python requirement updated to >=3.9
- ✅ License changed to Apache-2.0
- ✅ Project URLs added
- ✅ Version management uses importlib.metadata
- ✅ Release workflow created with Trusted Publishing
- ✅ Test workflow updated

## Setting Up PyPI Trusted Publishing

PyPI Trusted Publishing allows publishing packages without API tokens, using GitHub's OIDC provider for authentication.

### Step 1: Register Project Name on PyPI

1. Go to https://pypi.org/account/register/ (or log in if you already have an account)
2. Once logged in, go to your account settings
3. Navigate to "Publishing" → "Add a new pending publisher"
4. Fill in the following information:
   - **PyPI Project Name**: `guiderails`
   - **Owner**: `srbouffard`
   - **Repository name**: `guiderails`
   - **Workflow name**: `release.yml`
   - **Environment name**: (leave blank)
5. Click "Add"

This creates a "pending publisher" that will be activated when the first release is published via the GitHub workflow.

### Step 2: Create and Publish First Release

1. **Verify all tests pass**:
   ```bash
   # The GitHub Actions test workflow should be green
   ```

2. **Update CHANGELOG.md** (if not already done):
   ```markdown
   ## [0.1.0] - 2024-11-02
   
   ### Added
   - Initial PyPI release
   - CLI with `exec` subcommand for running tutorials
   - Support for guided and CI modes
   - [... other features ...]
   ```

3. **Create a Git tag**:
   ```bash
   git tag -a v0.1.0 -m "Release v0.1.0"
   git push origin v0.1.0
   ```

4. **Create GitHub Release**:
   - Go to https://github.com/srbouffard/guiderails/releases/new
   - Select the tag: `v0.1.0`
   - Release title: `v0.1.0`
   - Description: Copy from CHANGELOG.md or write release notes
   - Click "Publish release"

5. **Monitor the release workflow**:
   - Go to https://github.com/srbouffard/guiderails/actions
   - Watch the "Release to PyPI" workflow
   - It should:
     - Build the package
     - Publish to PyPI using Trusted Publishing
     - Complete successfully

### Step 3: Verify Publication

After the workflow completes:

1. Check PyPI: https://pypi.org/project/guiderails/
2. Test installation:
   ```bash
   pip install guiderails
   guiderails --version
   # Should output: guiderails, version 0.1.0
   ```

## Subsequent Releases

For future releases:

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Commit changes
4. Create tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
5. Push tag: `git push origin vX.Y.Z`
6. Create GitHub Release
7. Workflow automatically publishes to PyPI

## Troubleshooting

### "Publisher does not match" error

If you see an error about the publisher not matching:
- Verify the pending publisher settings in PyPI match exactly:
  - Owner: `srbouffard`
  - Repository: `guiderails`
  - Workflow: `release.yml`
- Check that the workflow is triggered from a tag or release event

### Build failures

If the build fails:
- Check that hatchling is installed in the workflow
- Verify pyproject.toml syntax
- Run `python -m build` locally to test

### Package not found after publication

- Wait a few minutes for PyPI's CDN to update
- Check https://pypi.org/project/guiderails/ directly
- Try with `pip install --no-cache-dir guiderails`

## Manual Publication (Not Recommended)

If Trusted Publishing setup fails, you can manually publish:

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Upload to PyPI (requires API token)
twine upload dist/*
```

However, this requires creating and managing API tokens, which Trusted Publishing eliminates.

## Testing Before Production

To test the release process without publishing to production PyPI:

1. Use TestPyPI instead:
   - Set up a separate pending publisher on https://test.pypi.org/
   - Modify the release workflow to use TestPyPI endpoint
   - Test the full release process

2. Install from TestPyPI:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ guiderails
   ```

## Resources

- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions + PyPI](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [Hatchling Documentation](https://hatch.pypa.io/latest/)
