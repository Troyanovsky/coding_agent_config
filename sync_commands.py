"""Sync command prompt files and related symlinks for multiple AI tool directories."""
from __future__ import annotations

import json
import os
import pathlib
import sys
import platform
from typing import Optional

# Try to import yaml for proper YAML front matter generation
# Falls back to manual escaping if not available
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Try to import tomli for parsing TOML files (Python 3.10 compatibility)
try:
    import tomli as tomllib
except ImportError:
    try:
        import tomllib # Python 3.11+
    except ImportError:
        print("Error: This script requires 'tomli' (Python < 3.11) or 'tomllib' (Python 3.11+).")
        print("Please run: pip install tomli")
        sys.exit(1)

# Module-level constants
CLAUDE_PREFIX = "claude_"

def safe_symlink(target: pathlib.Path, link_name: pathlib.Path) -> None:
    """
    Creates a symlink safely, handling Windows permission errors.
    """
    try:
        os.symlink(target, link_name)
        # Show full relative path from home directory (e.g., ".claude/agents/file.md")
        try:
            link_rel_path = link_name.relative_to(pathlib.Path.home())
            print(f"  Linked {target.name} -> {link_rel_path}")
        except ValueError:
            # Path not relative to home (e.g., in tests)
            print(f"  Linked {target.name} -> {link_name.parent.name}/{link_name.name}")
    except OSError as e:
        # Check for Windows specific error: [WinError 1314] A required privilege is not held by the client
        if platform.system() == "Windows" and getattr(e, 'winerror', 0) == 1314:
            print(f"  Error linking {target.name}: [WinError 1314] Insufficient privileges.")
            print("  -> Please enable 'Developer Mode' in Windows Settings or run this script as Administrator.")
        else:
            print(f"  Error linking {target.name}: {e}")

def safe_remove(file_path: pathlib.Path, context: Optional[str] = None) -> bool:
    """
    Removes a file or symlink safely, handling potential errors.

    Args:
        file_path: Path to the file or symlink to remove.
        context: Optional context string describing why the file is being removed.
    """
    try:
        if file_path.is_symlink() or file_path.is_file():
            file_path.unlink()
            print(f"  Removed {file_path.name}")
            return True
    except OSError as e:
        context_str = f" ({context})" if context else ""
        print(f"  Error removing {file_path.name}{context_str}: {e}")
    return False

def _get_output_stem(source_stem: str, strip_prefix: Optional[str]) -> Optional[str]:
    """
    Computes the output filename stem after optionally stripping a prefix.

    Args:
        source_stem: The source filename stem (without extension).
        strip_prefix: Optional prefix to strip from the stem. Pass None to skip
            stripping. Passing an empty string will trigger a warning and behave
            like None.

    Returns:
        The output stem after stripping, or None if the stem would be empty
        after stripping.
    """
    if strip_prefix == "":
        print("  Warning: strip_prefix is an empty string. Prefix stripping will be skipped.")

    if strip_prefix and source_stem.startswith(strip_prefix):
        result = source_stem[len(strip_prefix):]
        return result if result else None
    return source_stem


def _escape_yaml_string(value: str) -> str:
    """
    Escapes a string for safe use in YAML single-quoted style.

    In YAML single-quoted scalars, only single quotes are escaped by doubling.
    Backslashes are literal and should not be modified.
    """
    return value.replace("'", "''")


def _format_yaml_description(description: str) -> str:
    """
    Formats a description string for YAML front matter.

    Uses PyYAML if available for robust handling of all edge cases including
    multi-line strings. Falls back to single-quoted strings (no multi-line support).
    """
    if HAS_YAML:
        front_matter = yaml.dump(
            {"description": description},
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
        ).rstrip('\n')
        # PyYAML may prefix output with --- document marker; strip it to avoid
        # duplication when _write_prompt_file adds its own --- delimiters.
        if front_matter.startswith('---'):
            front_matter = front_matter[3:]
            # Remove only the single newline that follows the marker
            if front_matter.startswith('\n'):
                front_matter = front_matter[1:]
        return front_matter
    else:
        # Fallback: use YAML single-quoted string style.
        # Note: Manual construction doesn't add --- marker, so no stripping needed.
        # Single quotes in YAML require doubling single quotes and backslashes
        if '\n' in description:
            print("  Warning: Multi-line description requires PyYAML for proper YAML escaping.")
            print("  -> Newlines will be replaced with spaces. Install with: pip install pyyaml")
            description = description.replace('\n', ' ')
        escaped_desc = _escape_yaml_string(description)
        return f"description: '{escaped_desc}'"


def _write_prompt_file(target_file: pathlib.Path, prompt_content: str, description: Optional[str] = None) -> None:
    """
    Writes prompt content to a target file, optionally with YAML front matter.

    Uses proper YAML escaping for the description field to handle multi-line
    strings, special YAML characters (: []{!&*}), and Unicode correctly.
    """
    if description is not None:
        front_matter = _format_yaml_description(description)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(f"---\n{front_matter}\n---\n\n{prompt_content}")
    else:
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(prompt_content)


def _process_source_file(source_file: pathlib.Path, target_cmds_dir: pathlib.Path, tool_name: str, strip_prefix: Optional[str], include_description: bool) -> Optional[str]:
    """
    Processes a single source .toml file and extracts its prompt to a .md file.
    Returns the .md filename if successful, None otherwise.
    """
    try:
        with open(source_file, "rb") as f:
            data = tomllib.load(f)

        if "prompt" not in data:
            print(f"  Skipping {source_file.name}: no 'prompt' key.")
            return None

        prompt_content = data["prompt"]
        stem = _get_output_stem(source_file.stem, strip_prefix)

        if not stem:
            print(f"  Skipping {source_file.name}: stem is empty after stripping prefix.")
            return None

        md_filename = stem + ".md"
        target_file = target_cmds_dir / md_filename
        description = data.get("description", "") if include_description else None

        _write_prompt_file(target_file, prompt_content, description)

        subdir = "prompts" if include_description else "commands"
        print(f"  Extracted prompt from {source_file.name} -> {tool_name}/{subdir}/{md_filename}")
        return md_filename
    except (OSError, ValueError) as e:
        print(f"  Error processing {source_file.name} for {tool_name}: {e}")
        return None


def _should_remove_md_file(item: pathlib.Path, toml_files: list[pathlib.Path], created_md_files: set[str], strip_prefix: Optional[str]) -> bool:
    """
    Determines if a .md file should be removed during cleanup.

    DESIGN DECISION: All .md files are fully regenerated on each run.
    Files that match a source .toml but were NOT recreated in the current run
    are considered stale and removed. This ensures consistency and prevents
    orphaned files from accumulating.

    Returns True if the file should be removed, False otherwise.
    """
    item_stem = item.stem

    for source_file in toml_files:
        source_stem = source_file.stem
        expected_stem = _get_output_stem(source_stem, strip_prefix) or source_stem

        if item_stem == expected_stem:
            # File matches expected output - keep it if we just created it
            return item.name not in created_md_files
        elif strip_prefix and item_stem == source_stem:
            # File matches source name but should have been stripped (old format)
            return True

    return True


def _cleanup_stale_md_files(target_cmds_dir: pathlib.Path, toml_files: list[pathlib.Path], created_md_files: set[str], strip_prefix: Optional[str]) -> None:
    """
    Removes .md files that don't have corresponding source .toml files,
    including files with old naming format.
    """
    for item in target_cmds_dir.glob("*.md"):
        if _should_remove_md_file(item, toml_files, created_md_files, strip_prefix):
            safe_remove(item, context="stale .md file during cleanup")


def _cleanup_stale_symlinks(cmd_dir: pathlib.Path, source_files: list[pathlib.Path], source_dir_resolved: pathlib.Path) -> None:
    """
    Removes stale symlinks from a directory that point to non-existent source files.
    """
    source_names = {f.name for f in source_files}
    for item in cmd_dir.iterdir():
        if item.is_symlink():
            try:
                target = item.resolve()
                if target.parent == source_dir_resolved and target.name not in source_names:
                    safe_remove(item, context="stale symlink during cleanup")
            except OSError:
                safe_remove(item, context="broken symlink during cleanup")


def _sync_symlinks_to_dir(source_files: list[pathlib.Path], cmd_dir: pathlib.Path, source_dir_resolved: pathlib.Path) -> None:
    """
    Creates symlinks for source files in a target directory and cleans up stale symlinks.
    """
    cmd_dir.mkdir(parents=True, exist_ok=True)

    for source_file in source_files:
        link_name = cmd_dir / source_file.name
        expected_target = source_file.resolve()

        # Check if link already exists
        if link_name.exists() or link_name.is_symlink():
            # Verify existing symlink points to correct target
            try:
                current_target = link_name.resolve()
                # Use os.path.samefile for robust cross-platform path comparison
                # This handles /var -> /private/var symlinks on macOS and similar cases
                if os.path.samefile(current_target, expected_target):
                    # Correct symlink already exists - skip it
                    try:
                        link_rel_path = link_name.relative_to(pathlib.Path.home())
                        print(f"  Skipping {source_file.name}: symlink already exists in {link_rel_path.parent}")
                    except ValueError:
                        # Path not relative to home (e.g., in tests), use parent dir name
                        print(f"  Skipping {source_file.name}: symlink already exists in {link_name.parent.name}")
                    continue
                else:
                    # Incorrect symlink - remove and recreate
                    try:
                        link_rel_path = link_name.relative_to(pathlib.Path.home())
                        print(f"  Replacing incorrect symlink {source_file.name} in {link_rel_path.parent}")
                    except ValueError:
                        print(f"  Replacing incorrect symlink {source_file.name} in {link_name.parent.name}")
                    safe_remove(link_name, context="incorrect symlink")
            except OSError:
                # Broken symlink - remove and recreate
                try:
                    link_rel_path = link_name.relative_to(pathlib.Path.home())
                    print(f"  Replacing broken symlink {source_file.name} in {link_rel_path.parent}")
                except ValueError:
                    print(f"  Replacing broken symlink {source_file.name} in {link_name.parent.name}")
                safe_remove(link_name, context="broken symlink")

        # Create new symlink
        safe_symlink(expected_target, link_name)

    _cleanup_stale_symlinks(cmd_dir, source_files, source_dir_resolved)


def _sync_symlink_targets(shared_files: list[pathlib.Path], source_dir: pathlib.Path, targets_symlink: list[tuple[pathlib.Path, pathlib.Path]]) -> None:
    """
    Syncs symlinks for tools that use direct file symlinks (Gemini, Qwen, iflow).
    """
    source_dir_resolved = source_dir.resolve()
    for root_dir, cmd_dir in targets_symlink:
        if root_dir.exists():
            print(f"Processing {root_dir.name}...")
            _sync_symlinks_to_dir(shared_files, cmd_dir, source_dir_resolved)
        else:
            print(f"Skipping {root_dir.name}: directory does not exist.")


def _sync_agents_folder(target_claude_agents: pathlib.Path) -> None:
    """
    Syncs agent .md files from ./agents to .claude/agents.
    """
    print(f"\nProcessing agents folder symlinks...")

    agents_source_dir = pathlib.Path("./agents").resolve()
    if not agents_source_dir.exists() or not agents_source_dir.is_dir():
        print("  Skipping agents folder: source directory './agents' does not exist.")
        return

    agents_md_files: list[pathlib.Path] = list(agents_source_dir.glob("*.md"))
    if not agents_md_files:
        print("  No .md files found in ./agents/")
        return

    print(f"  Found {len(agents_md_files)} agent .md files.")
    _sync_symlinks_to_dir(agents_md_files, target_claude_agents, agents_source_dir.resolve())


def _create_agents_md_link(agents_md_source: pathlib.Path, root_dir: pathlib.Path, target_file_name: str) -> bool:
    """
    Creates a symlink for AGENTS.md to the specified target location.
    Returns True if the link was created or already exists.
    """
    if not root_dir.exists():
        print(f"Skipping {root_dir.name}: directory does not exist for AGENTS.md symlink.")
        return False

    link_path = root_dir / target_file_name
    if not link_path.exists() and not link_path.is_symlink():
        safe_symlink(agents_md_source, link_path)
    else:
        print(f"  Skipping AGENTS.md link to {root_dir.name}/{target_file_name}: already exists.")
    return True


def _remove_agents_md_link(root_dir: pathlib.Path, target_file_name: str) -> None:
    """
    Removes an AGENTS.md symlink from the specified location if it exists.
    """
    if root_dir.exists():
        link_path = root_dir / target_file_name
        if link_path.exists() or link_path.is_symlink():
            safe_remove(link_path, context="AGENTS.md symlink")


def _sync_agents_md_links(home: pathlib.Path) -> None:
    """
    Syncs AGENTS.md symlinks to various tool directories.
    """
    agents_md_source = pathlib.Path("AGENTS.md").resolve()
    print(f"\nProcessing AGENTS.md symlinks...")

    agents_md_targets: list[tuple[pathlib.Path, str]] = [
        (home / ".claude", "CLAUDE.md"),
        (home / ".gemini", "AGENTS.md"),
        (home / ".qwen", "QWEN.md"),
        (home / ".codex", "AGENTS.md"),
        (home / ".iflow", "IFLOW.md"),
    ]

    if agents_md_source.exists():
        for root_dir, target_file_name in agents_md_targets:
            _create_agents_md_link(agents_md_source, root_dir, target_file_name)

        # Handle Roo AGENTS.md symlink to ~/.roo/rules/AGENTS.md
        target_roo_root = home / ".roo"
        if target_roo_root.exists():
            target_roo_rules = home / ".roo" / "rules"
            target_roo_rules.mkdir(parents=True, exist_ok=True)
            _create_agents_md_link(agents_md_source, target_roo_rules, "AGENTS.md")
        else:
            print("Skipping .roo: directory does not exist for AGENTS.md symlink.")
    else:
        print(f"Warning: Source file '{agents_md_source}' not found. Removing existing AGENTS.md symlinks...")
        for root_dir, target_file_name in agents_md_targets:
            _remove_agents_md_link(root_dir, target_file_name)

        target_roo_root = home / ".roo"
        if target_roo_root.exists():
            target_roo_rules = home / ".roo" / "rules"
            _remove_agents_md_link(target_roo_rules, "AGENTS.md")


def extract_prompts_to_md(toml_files: list[pathlib.Path], target_cmds_dir: pathlib.Path, tool_name: str, strip_prefix: Optional[str] = None) -> None:
    """
    Extracts prompts from .toml files to .md files in the target directory,
    and removes stale .md files that no longer have corresponding source files.

    Args:
        toml_files: List of source .toml file paths
        target_cmds_dir: Target directory for .md files
        tool_name: Name of the tool (for logging purposes)
        strip_prefix: Optional prefix to strip from output filenames
    """
    print(f"Processing {tool_name}...")
    target_cmds_dir.mkdir(parents=True, exist_ok=True)

    created_md_files: set[str] = set()
    for source_file in toml_files:
        result = _process_source_file(source_file, target_cmds_dir, tool_name, strip_prefix, include_description=False)
        if result:
            created_md_files.add(result)

    _cleanup_stale_md_files(target_cmds_dir, toml_files, created_md_files, strip_prefix)

def extract_prompts_to_md_with_description(toml_files: list[pathlib.Path], target_cmds_dir: pathlib.Path, tool_name: str, strip_prefix: Optional[str] = None) -> None:
    """
    Extracts prompts and descriptions from .toml files to .md files with YAML front matter,
    and removes stale .md files that no longer have corresponding source files.

    The output format is:
    ---
    description: {description}
    ---

    {prompt}

    Args:
        toml_files: List of source .toml file paths
        target_cmds_dir: Target directory for .md files
        tool_name: Name of the tool (for logging purposes)
        strip_prefix: Optional prefix to strip from output filenames
    """
    print(f"Processing {tool_name}...")
    target_cmds_dir.mkdir(parents=True, exist_ok=True)

    created_md_files: set[str] = set()
    for source_file in toml_files:
        result = _process_source_file(source_file, target_cmds_dir, tool_name, strip_prefix, include_description=True)
        if result:
            created_md_files.add(result)

    _cleanup_stale_md_files(target_cmds_dir, toml_files, created_md_files, strip_prefix)

def main() -> None:
    """Main entry point for syncing command files to various AI tool directories."""
    # Source directory
    source_dir = pathlib.Path("./commands")
    if not source_dir.exists() or not source_dir.is_dir():
        print(f"Error: Source directory '{source_dir}' not found while locating commands directory.")
        return

    # Get all .toml files
    toml_files: list[pathlib.Path] = list(source_dir.glob("*.toml"))
    if not toml_files:
        print("No .toml files found in ./commands/")
        return

    print(f"Found {len(toml_files)} .toml files.")

    # Filter files: claude_ prefixed commands only go to Claude, others go to all tools
    claude_only_files: list[pathlib.Path] = [f for f in toml_files if f.stem.startswith(CLAUDE_PREFIX)]
    shared_files: list[pathlib.Path] = [f for f in toml_files if not f.stem.startswith(CLAUDE_PREFIX)]

    print(f"  Claude-only commands ({CLAUDE_PREFIX}*): {len(claude_only_files)}")
    print(f"  Shared commands: {len(shared_files)}")

    # Define targets
    home = pathlib.Path.home()

    targets_symlink: list[tuple[pathlib.Path, pathlib.Path]] = [
        (home / ".gemini", home / ".gemini" / "commands"),
        (home / ".qwen", home / ".qwen" / "commands"),
        (home / ".iflow", home / ".iflow" / "commands"),
    ]

    target_claude_root = home / ".claude"
    target_claude_cmds = home / ".claude" / "commands"
    target_claude_agents = home / ".claude" / "agents"

    # 1. Handle Symlinks (Gemini, Qwen, iflow) - only shared files
    _sync_symlink_targets(shared_files, source_dir, targets_symlink)

    # 2. Handle Claude (Extraction) - all files, strip claude_ prefix
    if target_claude_root.exists():
        extract_prompts_to_md(toml_files, target_claude_cmds, ".claude", strip_prefix=CLAUDE_PREFIX)
    else:
        print("Skipping .claude: directory does not exist.")

    # 3. Handle Roo (Extraction) - only shared files
    target_roo_root = home / ".roo"
    target_roo_cmds = home / ".roo" / "commands"
    if target_roo_root.exists():
        extract_prompts_to_md(shared_files, target_roo_cmds, ".roo")
    else:
        print("Skipping .roo: directory does not exist.")

    # 4. Handle Codex (Extraction with Description) - only shared files
    target_codex_root = home / ".codex"
    target_codex_prompts = home / ".codex" / "prompts"
    if target_codex_root.exists():
        extract_prompts_to_md_with_description(shared_files, target_codex_prompts, ".codex")
    else:
        print("Skipping .codex: directory does not exist.")

    # 5. Handle Agents Folder Symlinks to Claude Code
    if target_claude_root.exists():
        _sync_agents_folder(target_claude_agents)
    else:
        print("  Skipping agents folder: .claude directory does not exist.")

    # 6. Handle AGENTS.md Symlinks
    _sync_agents_md_links(home)

if __name__ == "__main__":
    main()
