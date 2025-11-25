#!/usr/bin/env python3
"""
Release Automation Engine

Automates versioning, changelog generation, and Git tagging for releases.
"""

import os
import sys
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Optional


class Version:
    """Semantic version"""
    
    def __init__(self, major: int, minor: int, patch: int, prerelease: Optional[str] = None):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.prerelease = prerelease
    
    def __str__(self):
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        return version
    
    @classmethod
    def parse(cls, version_str: str) -> 'Version':
        """Parse version string"""
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$', version_str)
        if not match:
            raise ValueError(f"Invalid version format: {version_str}")
        
        major, minor, patch = map(int, match.groups()[:3])
        prerelease = match.group(4)
        return cls(major, minor, patch, prerelease)
    
    def bump_major(self) -> 'Version':
        """Bump major version"""
        return Version(self.major + 1, 0, 0)
    
    def bump_minor(self) -> 'Version':
        """Bump minor version"""
        return Version(self.major, self.minor + 1, 0)
    
    def bump_patch(self) -> 'Version':
        """Bump patch version"""
        return Version(self.major, self.minor, self.patch + 1)


def get_current_version() -> Version:
    """Get current version from various sources"""
    # Check package.json (frontend)
    package_json = Path("frontend/package.json")
    if package_json.exists():
        import json
        data = json.loads(package_json.read_text())
        if "version" in data:
            return Version.parse(data["version"])
    
    # Check pyproject.toml (backend)
    pyproject_toml = Path("pyproject.toml")
    if pyproject_toml.exists():
        content = pyproject_toml.read_text()
        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return Version.parse(match.group(1))
    
    # Check VERSION file
    version_file = Path("VERSION")
    if version_file.exists():
        return Version.parse(version_file.read_text().strip())
    
    # Default
    return Version(1, 0, 0)


def set_version(version: Version):
    """Set version in all relevant files"""
    version_str = str(version)
    
    # Update package.json
    package_json = Path("frontend/package.json")
    if package_json.exists():
        import json
        data = json.loads(package_json.read_text())
        data["version"] = version_str
        package_json.write_text(json.dumps(data, indent=2) + "\n")
        print(f"✅ Updated frontend/package.json: {version_str}")
    
    # Update VERSION file
    version_file = Path("VERSION")
    version_file.write_text(version_str + "\n")
    print(f"✅ Updated VERSION: {version_str}")
    
    # Update pyproject.toml if exists
    pyproject_toml = Path("pyproject.toml")
    if pyproject_toml.exists():
        content = pyproject_toml.read_text()
        content = re.sub(
            r'version\s*=\s*["\'][^"\']+["\']',
            f'version = "{version_str}"',
            content
        )
        pyproject_toml.write_text(content)
        print(f"✅ Updated pyproject.toml: {version_str}")


def get_git_commits_since_tag(tag: Optional[str] = None) -> List[dict]:
    """Get git commits since last tag"""
    cmd = ["git", "log", "--pretty=format:%h|%s|%an|%ad", "--date=short"]
    
    if tag:
        cmd.extend([f"{tag}..HEAD"])
    else:
        # Get commits since last tag
        result = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            last_tag = result.stdout.strip()
            cmd.extend([f"{last_tag}..HEAD"])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    
    commits = []
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split('|', 3)
        if len(parts) >= 2:
            commits.append({
                'hash': parts[0],
                'message': parts[1],
                'author': parts[2] if len(parts) > 2 else 'Unknown',
                'date': parts[3] if len(parts) > 3 else ''
            })
    
    return commits


def categorize_commits(commits: List[dict]) -> dict:
    """Categorize commits by type"""
    categories = {
        'feat': [],
        'fix': [],
        'docs': [],
        'style': [],
        'refactor': [],
        'perf': [],
        'test': [],
        'chore': [],
        'other': []
    }
    
    for commit in commits:
        message = commit['message']
        categorized = False
        
        for category in categories.keys():
            if message.startswith(f"{category}:"):
                categories[category].append(commit)
                categorized = True
                break
        
        if not categorized:
            categories['other'].append(commit)
    
    return categories


def generate_changelog(version: Version, commits: List[dict]) -> str:
    """Generate changelog entry"""
    categories = categorize_commits(commits)
    
    changelog = f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n\n"
    
    # Features
    if categories['feat']:
        changelog += "### Added\n"
        for commit in categories['feat']:
            message = commit['message'].replace('feat:', '').strip()
            changelog += f"- {message}\n"
        changelog += "\n"
    
    # Fixes
    if categories['fix']:
        changelog += "### Fixed\n"
        for commit in categories['fix']:
            message = commit['message'].replace('fix:', '').strip()
            changelog += f"- {message}\n"
        changelog += "\n"
    
    # Other changes
    other_categories = ['docs', 'style', 'refactor', 'perf', 'test', 'chore']
    other_changes = []
    for cat in other_categories:
        other_changes.extend(categories[cat])
    
    if other_changes:
        changelog += "### Changed\n"
        for commit in other_changes:
            message = commit['message']
            # Remove category prefix if present
            for cat in other_categories:
                if message.startswith(f"{cat}:"):
                    message = message.replace(f"{cat}:", '').strip()
                    break
            changelog += f"- {message}\n"
        changelog += "\n"
    
    return changelog


def update_changelog(version: Version, commits: List[dict]):
    """Update CHANGELOG.md"""
    changelog_file = Path("CHANGELOG.md")
    
    if not changelog_file.exists():
        content = "# Changelog\n\n"
        content += "All notable changes to this project will be documented in this file.\n\n"
        content += "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),\n"
        content += "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"
    else:
        content = changelog_file.read_text()
    
    # Insert new changelog entry after header
    new_entry = generate_changelog(version, commits)
    
    # Find insertion point (after header, before first ##)
    lines = content.split('\n')
    insert_index = 0
    for i, line in enumerate(lines):
        if line.startswith('## ['):
            insert_index = i
            break
    
    lines.insert(insert_index, new_entry)
    content = '\n'.join(lines)
    
    changelog_file.write_text(content)
    print(f"✅ Updated CHANGELOG.md")


def create_git_tag(version: Version, message: Optional[str] = None):
    """Create git tag"""
    tag = f"v{version}"
    tag_message = message or f"Release {version}"
    
    subprocess.run(["git", "tag", "-a", tag, "-m", tag_message], check=True)
    print(f"✅ Created git tag: {tag}")


def main():
    """Main CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Release automation")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Manage version")
    version_parser.add_argument("action", choices=["current", "bump"], help="Action")
    version_parser.add_argument("--type", choices=["major", "minor", "patch"], 
                               help="Bump type")
    
    # Release command
    release_parser = subparsers.add_parser("release", help="Create release")
    release_parser.add_argument("--type", choices=["major", "minor", "patch"], 
                               default="patch", help="Release type")
    release_parser.add_argument("--dry-run", action="store_true", 
                               help="Dry run (don't commit)")
    release_parser.add_argument("--skip-tag", action="store_true", 
                               help="Skip git tag creation")
    
    args = parser.parse_args()
    
    if args.command == "version":
        current = get_current_version()
        if args.action == "current":
            print(f"Current version: {current}")
        elif args.action == "bump":
            if args.type == "major":
                new_version = current.bump_major()
            elif args.type == "minor":
                new_version = current.bump_minor()
            else:
                new_version = current.bump_patch()
            
            set_version(new_version)
            print(f"Bumped version: {current} → {new_version}")
    
    elif args.command == "release":
        current = get_current_version()
        
        # Bump version
        if args.type == "major":
            new_version = current.bump_major()
        elif args.type == "minor":
            new_version = current.bump_minor()
        else:
            new_version = current.bump_patch()
        
        print(f"Creating release {new_version}...")
        
        # Get commits since last tag
        commits = get_git_commits_since_tag()
        
        if not commits:
            print("⚠️  No commits since last tag")
            return
        
        # Update version
        set_version(new_version)
        
        # Update changelog
        update_changelog(new_version, commits)
        
        if not args.dry_run:
            # Commit changes
            subprocess.run(["git", "add", "VERSION", "CHANGELOG.md", 
                          "frontend/package.json"], check=True)
            subprocess.run(["git", "commit", "-m", f"chore: release {new_version}"], 
                         check=True)
            
            # Create tag
            if not args.skip_tag:
                create_git_tag(new_version)
            
            print(f"\n✅ Release {new_version} created!")
            print(f"   Commits: {len(commits)}")
            print(f"   Next: git push && git push --tags")
        else:
            print(f"\n✅ Dry run complete - release {new_version} would be created")
            print(f"   Commits: {len(commits)}")


if __name__ == "__main__":
    main()
