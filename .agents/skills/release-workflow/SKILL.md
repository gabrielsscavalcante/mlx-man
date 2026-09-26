---
name: release-workflow
description: >-
  Prepares and cuts tagged software releases for MLX-Man following strict SemVer,
  pre-flight verification, changelog updates, and safe Git tagging standards.
  Use whenever cutting a new release, bumping versions, or preparing a release tag.
---

# MLX-Man Release Workflow Skill

This skill guides the preparation, verification, and tagging of a new release for **MLX-Man**.

## Mandatory Safety Rules

1. **Main Branch Only**: Releases and Git tags MUST only be created directly on the `main` branch. Never tag a feature branch.
2. **Clean Working Tree**: Ensure `git status` shows no unstaged, uncommitted, or untracked changes before starting.
3. **Pre-flight Tests**: All tests (`pytest tests/`) must pass before cutting any release.
4. **Push Confirmation**: Strictly follow the **No Push Without Confirmation** rule. Never run `git push origin vX.Y.Z` or `git push origin main` without prior explicit approval.

---

## Release Procedure

### Step 1: Pre-Release Verification
Ensure all feature PRs have been reviewed, tested, and merged into `main`:
```bash
git checkout main
git pull origin main
uv run pytest tests/ -v
```

### Step 2: Dry-Run Release
Preview the release and verify version computation:
```bash
./scripts/release.sh patch --dry-run
# Or minor / major / x.y.z
```

### Step 3: Execute Release
Run the automated release script:
```bash
./scripts/release.sh [patch|minor|major|x.y.z]
```
This script automatically:
1. Calculates the next SemVer version.
2. Synchronizes version across `src/mlx_man/__init__.py`, `pyproject.toml`, and `tests/test_setup.py`.
3. Runs `scripts/update_docs.py` to auto-extract git commits into `CHANGELOG.md` and check `Documentation.md`.
4. Builds the package wheel and tarball using `uv build`.
5. Verifies package importability.
6. Commits the changes and creates the annotated Git tag (e.g. `v0.5.0`) locally.

### Step 4: Publish Release
Ask the user for explicit confirmation before pushing:
> "Release vX.Y.Z has been tested and tagged locally. Are you ready for me to push the commit and tag to the remote repository to trigger the GitHub Release?"

Once approved, push:
```bash
git push origin main
git push origin vX.Y.Z
```

GitHub Actions will then automatically build distribution artifacts and publish the GitHub Release with attached `.whl` and `.tar.gz` files.
