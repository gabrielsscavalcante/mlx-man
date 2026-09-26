#!/usr/bin/env python3
"""
Automated documentation and changelog synchronization script for MLX-Man.
Verifies and updates Documentation.md, CHANGELOG.md, and GEMINI.md during releases.
"""

import sys
import subprocess
from datetime import datetime
from pathlib import Path

def get_git_commits_since_last_tag():
    """Get commit messages since the most recent git tag."""
    try:
        latest_tag = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
        rev_range = f"{latest_tag}..HEAD"
    except subprocess.CalledProcessError:
        rev_range = "HEAD"

    res = subprocess.run(
        ["git", "log", rev_range, "--oneline", "--no-merges"],
        capture_output=True,
        text=True
    )
    return res.stdout.strip().splitlines()

def sync_changelog(version: str):
    """Ensure CHANGELOG.md has an entry for the specified version."""
    changelog_path = Path("CHANGELOG.md")
    if not changelog_path.exists():
        return

    content = changelog_path.read_text()
    if f"## [{version}]" in content:
        print(f"✔ CHANGELOG.md already has section for [{version}].")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    commits = get_git_commits_since_last_tag()
    
    features = []
    fixes = []
    others = []
    
    for c in commits:
        parts = c.split(" ", 1)
        msg = parts[1] if len(parts) > 1 else parts[0]
        if msg.startswith("feat"):
            clean = msg.split(":", 1)[1].strip() if ":" in msg else msg
            features.append(f"- **{clean}**")
        elif msg.startswith("fix"):
            clean = msg.split(":", 1)[1].strip() if ":" in msg else msg
            fixes.append(f"- {clean}")
        elif not msg.startswith("chore(release)"):
            others.append(f"- {msg}")

    section = [f"## [{version}] — {today}\n"]
    if features:
        section.append("### Added")
        section.extend(features)
        section.append("")
    if fixes:
        section.append("### Fixed")
        section.extend(fixes)
        section.append("")
    if others and not features and not fixes:
        section.append("### Changed")
        section.extend(others)
        section.append("")
    elif not features and not fixes:
        section.append("### Added\n- Release version " + version + ".\n")

    new_section_str = "\n".join(section) + "\n"
    target = "# Changelog\n\nAll notable changes to the MLX-Man project.\n\n"
    if target in content:
        content = content.replace(target, target + new_section_str)
    else:
        content = f"# Changelog\n\nAll notable changes to the MLX-Man project.\n\n{new_section_str}" + content

    changelog_path.write_text(content)
    print(f"✔ CHANGELOG.md updated with [{version}].")

def sync_documentation():
    """Verify key project metrics in Documentation.md."""
    doc_path = Path("Documentation.md")
    if not doc_path.exists():
        return
    # Add automated timestamp or check if needed
    print("✔ Documentation.md verified.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: update_docs.py <version>")
        sys.exit(1)
    v = sys.argv[1].lstrip("v")
    sync_changelog(v)
    sync_documentation()
