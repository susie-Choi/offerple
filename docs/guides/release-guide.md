# Release Management Guide

This guide explains how to create and manage releases for ROTA.

## Release Process Overview

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit changes
4. Create and push git tag
5. GitHub Actions automatically:
   - Creates GitHub Release
   - Publishes to PyPI

## Step-by-Step Instructions

### 1. Prepare Release

Update version and changelog:

```bash
# Edit pyproject.toml - bump version
# Edit CHANGELOG.md - add release notes

git add pyproject.toml CHANGELOG.md
git commit -m "chore: Prepare release v0.1.4"
git push origin main
```

### 2. Create Release (Option A: Automated Script)

**Windows (PowerShell):**
```powershell
.\scripts\create_release.ps1 0.1.4
```

**Linux/Mac:**
```bash
chmod +x scripts/create_release.sh
./scripts/create_release.sh 0.1.4
```

### 3. Create Release (Option B: Manual)

```bash
# Create tag
git tag -a v0.1.4 -m "Release version 0.1.4"

# Push tag
git push origin v0.1.4
```

### 4. Verify Release

1. **GitHub Release**: https://github.com/susie-Choi/rota/releases
   - Check that release was created
   - Verify release notes from CHANGELOG

2. **PyPI**: https://pypi.org/project/rota/
   - Wait 1-2 minutes for Actions to complete
   - Verify new version is published

3. **Test Installation**:
   ```bash
   pip install --upgrade rota
   rota --version
   ```

## Release Checklist

Before creating a release:

- [ ] All tests passing
- [ ] Version bumped in `pyproject.toml`
- [ ] `CHANGELOG.md` updated with release notes
- [ ] Documentation updated if needed
- [ ] All changes committed and pushed to main
- [ ] Working directory is clean

## Version Numbering

ROTA follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backwards compatible
- **PATCH** (0.0.1): Bug fixes, backwards compatible

Examples:
- `0.1.3` → `0.1.4`: Bug fixes or minor improvements
- `0.1.3` → `0.2.0`: New features added
- `0.1.3` → `1.0.0`: Major release or breaking changes

## CHANGELOG Format

Follow [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [0.1.4] - 2025-10-28

### Added
- New feature X
- New feature Y

### Changed
- Improved Z

### Fixed
- Bug fix A
- Bug fix B

### Removed
- Deprecated feature C
```

## Troubleshooting

### Tag Already Exists

```bash
# Delete local tag
git tag -d v0.1.4

# Delete remote tag
git push origin :refs/tags/v0.1.4

# Recreate tag
git tag -a v0.1.4 -m "Release version 0.1.4"
git push origin v0.1.4
```

### Release Failed to Create

1. Check GitHub Actions logs
2. Verify `GITHUB_TOKEN` permissions
3. Manually create release on GitHub

### PyPI Upload Failed

1. Check if version already exists on PyPI
2. Verify `PYPI_API_TOKEN` secret is set
3. Check Actions logs for error details
4. Manually upload if needed:
   ```bash
   python -m build
   python -m twine upload dist/*
   ```

## Automated Workflows

### On Tag Push (`v*`)
- Creates GitHub Release with CHANGELOG notes
- Publishes to PyPI

### On Main Branch Push (with version change)
- Automatically publishes to PyPI

## Best Practices

1. **Always test before releasing**: Run tests locally
2. **Write clear changelog**: Help users understand changes
3. **Use semantic versioning**: Makes version numbers meaningful
4. **Tag from main branch**: Ensure stable release point
5. **Verify after release**: Check GitHub and PyPI

## Emergency Rollback

If a release has critical issues:

1. **Yank from PyPI** (doesn't delete, marks as unavailable):
   ```bash
   pip install twine
   twine upload --skip-existing dist/*  # Won't work, need to yank via web
   ```
   Go to https://pypi.org/manage/project/rota/releases/ and yank the version

2. **Create hotfix release**:
   ```bash
   # Fix the issue
   git commit -m "fix: Critical bug in v0.1.4"
   
   # Release patch version
   ./scripts/create_release.sh 0.1.5
   ```

3. **Update documentation**: Warn users about the problematic version

## Resources

- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [PyPI Publishing](https://packaging.python.org/tutorials/packaging-projects/)
