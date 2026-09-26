#!/usr/bin/env bash
# ==============================================================================
# MLX-Man Automated Release Script
# Prepares, tests, bumps version, updates changelog, and creates git release tag.
#
# Usage:
#   ./scripts/release.sh [patch|minor|major|<x.y.z>] [--dry-run]
# ==============================================================================

set -euo pipefail

DRY_RUN=false
TARGET_TYPE=""

for arg in "$@"; do
    case "$arg" in
        --dry-run)
            DRY_RUN=true
            ;;
        patch|minor|major|[0-9]*.[0-9]*.[0-9]*)
            TARGET_TYPE="$arg"
            ;;
        *)
            echo "❌ Unknown argument: $arg"
            echo "Usage: $0 [patch|minor|major|<x.y.z>] [--dry-run]"
            exit 1
            ;;
    esac
done

if [ -z "$TARGET_TYPE" ]; then
    echo "❌ Missing release version or bump type."
    echo "Usage: $0 [patch|minor|major|<x.y.z>] [--dry-run]"
    exit 1
fi

# 1. Enforce git safety: must be on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ] && [ "$DRY_RUN" = false ]; then
    echo "❌ Error: Releases must only be cut directly on the 'main' branch."
    echo "   Current branch is: $CURRENT_BRANCH"
    exit 1
fi

# 2. Enforce clean working directory
if [ -n "$(git status --porcelain)" ] && [ "$DRY_RUN" = false ]; then
    echo "❌ Error: Working tree has uncommitted changes. Please commit or stash them first."
    git status -s
    exit 1
fi

# 3. Read current version
CURRENT_VERSION=$(uv run python -c "import mlx_man; print(mlx_man.__version__)")
echo "📦 Current version: $CURRENT_VERSION"

# 4. Compute next version
NEXT_VERSION=$(uv run python -c "
cur = '$CURRENT_VERSION'.split('.')
major, minor, patch = int(cur[0]), int(cur[1]), int(cur[2])
tt = '$TARGET_TYPE'
if tt == 'major':
    print(f'{major + 1}.0.0')
elif tt == 'minor':
    print(f'{major}.{minor + 1}.0')
elif tt == 'patch':
    print(f'{major}.{minor}.{patch + 1}')
else:
    print(tt)
")

echo "🚀 Target version:  $NEXT_VERSION"

if [ "$CURRENT_VERSION" = "$NEXT_VERSION" ]; then
    echo "❌ Target version must be different from current version."
    exit 1
fi

# 5. Run test verification
echo "🧪 Running full test suite pre-flight check..."
uv run pytest tests/ -v --quiet

# 6. Apply version bump
echo "📝 Updating version across files..."
if [ "$DRY_RUN" = true ]; then
    echo "   [DRY-RUN] Would update src/mlx_man/__init__.py, pyproject.toml, tests/test_setup.py"
    echo "   [DRY-RUN] Would build package and create git tag v$NEXT_VERSION"
    exit 0
fi

python3 -c "
with open('src/mlx_man/__init__.py', 'r') as f:
    text = f.read()
text = text.replace('__version__ = \"$CURRENT_VERSION\"', '__version__ = \"$NEXT_VERSION\"')
with open('src/mlx_man/__init__.py', 'w') as f:
    f.write(text)

with open('pyproject.toml', 'r') as f:
    text = f.read()
text = text.replace('version = \"$CURRENT_VERSION\"', 'version = \"$NEXT_VERSION\"')
with open('pyproject.toml', 'w') as f:
    f.write(text)

with open('tests/test_setup.py', 'r') as f:
    text = f.read()
text = text.replace('assert mlx_man.__version__ == \"$CURRENT_VERSION\"', 'assert mlx_man.__version__ == \"$NEXT_VERSION\"')
with open('tests/test_setup.py', 'w') as f:
    f.write(text)
"

# 7. Update CHANGELOG.md if release section doesn't exist yet
TODAY=$(date +%Y-%m-%d)
if ! grep -q "## \[$NEXT_VERSION\]" CHANGELOG.md; then
    python3 -c "
with open('CHANGELOG.md', 'r') as f:
    content = f.read()

header = '## [$NEXT_VERSION] — $TODAY\n\n### Added\n- Release version $NEXT_VERSION.\n\n'
new_content = content.replace('# Changelog\n\nAll notable changes to the MLX-Man project.\n\n', '# Changelog\n\nAll notable changes to the MLX-Man project.\n\n' + header)
with open('CHANGELOG.md', 'w') as f:
    f.write(new_content)
"
    echo "   Updated CHANGELOG.md"
fi

# 8. Test package build
echo "📦 Testing distribution build..."
uv build

# 9. Verify updated test suite
uv run pytest tests/test_setup.py -v

# 10. Git commit and tag
git add src/mlx_man/__init__.py pyproject.toml tests/test_setup.py CHANGELOG.md
git commit -m "chore(release): bump version to v$NEXT_VERSION"
git tag -a "v$NEXT_VERSION" -m "Release v$NEXT_VERSION"

echo ""
echo "🎉 Release v$NEXT_VERSION successfully prepared and tagged locally!"
echo "   Tag: v$NEXT_VERSION"
echo ""
echo "👉 To publish the release to GitHub, run:"
echo "   git push origin main"
echo "   git push origin v$NEXT_VERSION"
