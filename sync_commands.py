import json
import os
import pathlib
import sys
import platform

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

def safe_symlink(target, link_name):
    """
    Creates a symlink safely, handling Windows permission errors.
    """
    try:
        os.symlink(target, link_name)
        print(f"  Linked {target.name} -> {link_name.parent.name}/{link_name.name}")
    except OSError as e:
        # Check for Windows specific error: [WinError 1314] A required privilege is not held by the client
        if platform.system() == "Windows" and getattr(e, 'winerror', 0) == 1314:
            print(f"  Error linking {target.name}: [WinError 1314] Insufficient privileges.")
            print("  -> Please enable 'Developer Mode' in Windows Settings or run this script as Administrator.")
        else:
            print(f"  Error linking {target.name}: {e}")

def safe_remove(file_path):
    """
    Removes a file or symlink safely, handling potential errors.
    """
    try:
        if file_path.is_symlink() or file_path.is_file():
            file_path.unlink()
            print(f"  Removed {file_path.name}")
            return True
    except OSError as e:
        print(f"  Error removing {file_path.name}: {e}")
    return False

def extract_prompts_to_md(toml_files, target_cmds_dir, tool_name):
    """
    Extracts prompts from .toml files to .md files in the target directory,
    and removes stale .md files that no longer have corresponding source files.

    Args:
        toml_files: List of source .toml file paths
        target_cmds_dir: Target directory for .md files
        tool_name: Name of the tool (for logging purposes)
    """
    print(f"Processing {tool_name}...")
    target_cmds_dir.mkdir(parents=True, exist_ok=True)

    # Track which .md files we create/update
    created_md_files = set()

    for source_file in toml_files:
        try:
            with open(source_file, "rb") as f:
                data = tomllib.load(f)

            if "prompt" in data:
                prompt_content = data["prompt"]
                # Create .md filename
                md_filename = source_file.stem + ".md"
                target_file = target_cmds_dir / md_filename
                created_md_files.add(md_filename)

                # Write extracted prompt
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(prompt_content)

                print(f"  Extracted prompt from {source_file.name} -> {tool_name}/commands/{md_filename}")
            else:
                print(f"  Skipping {source_file.name}: no 'prompt' key.")
        except OSError as e:
            print(f"  Error processing {source_file.name} for {tool_name}: {e}")

    # Cleanup: Remove .md files that don't have corresponding source .toml files
    for item in target_cmds_dir.glob("*.md"):
        if item.name not in created_md_files:
            safe_remove(item)

def extract_prompts_to_md_with_description(toml_files, target_cmds_dir, tool_name):
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
    """
    print(f"Processing {tool_name}...")
    target_cmds_dir.mkdir(parents=True, exist_ok=True)

    # Track which .md files we create/update
    created_md_files = set()

    for source_file in toml_files:
        try:
            with open(source_file, "rb") as f:
                data = tomllib.load(f)

            if "prompt" in data:
                prompt_content = data["prompt"]
                description = data.get("description", "")
                # Create .md filename
                md_filename = source_file.stem + ".md"
                target_file = target_cmds_dir / md_filename
                created_md_files.add(md_filename)

                # Write with YAML front matter (escaped for safety)
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(f"---\ndescription: {json.dumps(description)}\n---\n\n{prompt_content}")

                print(f"  Extracted prompt from {source_file.name} -> {tool_name}/prompts/{md_filename}")
            else:
                print(f"  Skipping {source_file.name}: no 'prompt' key.")
        except OSError as e:
            print(f"  Error processing {source_file.name} for {tool_name}: {e}")

    # Cleanup: Remove .md files that don't have corresponding source .toml files
    for item in target_cmds_dir.glob("*.md"):
        if item.name not in created_md_files:
            safe_remove(item)

def main():
    # Source directory
    source_dir = pathlib.Path("./commands")
    if not source_dir.exists() or not source_dir.is_dir():
        print(f"Error: Source directory '{source_dir}' not found.")
        return

    # Get all .toml files
    toml_files = list(source_dir.glob("*.toml"))
    if not toml_files:
        print("No .toml files found in ./commands/")
        return

    print(f"Found {len(toml_files)} .toml files.")

    # Define targets
    home = pathlib.Path.home()
    
    targets_symlink = [
        (home / ".gemini", home / ".gemini" / "commands"),
        (home / ".qwen", home / ".qwen" / "commands"),
        (home / ".iflow", home / ".iflow" / "commands"),
    ]
    
    target_claude_root = home / ".claude"
    target_claude_cmds = home / ".claude" / "commands"

    # 1. Handle Symlinks (Gemini & Qwen)
    for root_dir, cmd_dir in targets_symlink:
        if root_dir.exists():
            print(f"Processing {root_dir.name}...")
            cmd_dir.mkdir(parents=True, exist_ok=True)

            # Create or update symlinks
            for source_file in toml_files:
                link_name = cmd_dir / source_file.name

                # Check if link/file already exists
                if link_name.exists() or link_name.is_symlink():
                    print(f"  Skipping {source_file.name}: symlink already exists in {cmd_dir.name}")
                    continue

                # Create symlink (absolute path for safety)
                safe_symlink(source_file.resolve(), link_name)

            # Cleanup: Remove stale symlinks (symlinks pointing to non-existent source files)
            source_names = {f.name for f in toml_files}
            source_dir_resolved = source_dir.resolve()
            for item in cmd_dir.iterdir():
                if item.is_symlink():
                    try:
                        target = item.resolve()
                        # Check if the symlink target is in our source directory and still exists
                        if target.parent == source_dir_resolved and target.name not in source_names:
                            safe_remove(item)
                    except OSError:
                        # Broken symlink, remove it
                        safe_remove(item)
        else:
            print(f"Skipping {root_dir.name}: directory does not exist.")

    # 2. Handle Claude (Extraction)
    if target_claude_root.exists():
        extract_prompts_to_md(toml_files, target_claude_cmds, ".claude")
    else:
        print("Skipping .claude: directory does not exist.")

    # 3. Handle Roo (Extraction)
    target_roo_root = home / ".roo"
    target_roo_cmds = home / ".roo" / "commands"
    if target_roo_root.exists():
        extract_prompts_to_md(toml_files, target_roo_cmds, ".roo")
    else:
        print("Skipping .roo: directory does not exist.")

    # 4. Handle Codex (Extraction with Description)
    target_codex_root = home / ".codex"
    target_codex_prompts = home / ".codex" / "prompts"
    if target_codex_root.exists():
        extract_prompts_to_md_with_description(toml_files, target_codex_prompts, ".codex")
    else:
        print("Skipping .codex: directory does not exist.")

    # 5. Handle AGENTS.md Symlinks
    agents_md_source = pathlib.Path("AGENTS.md").resolve()
    print(f"\nProcessing AGENTS.md symlinks...")

    # Define target configurations for AGENTS.md
    agents_md_targets = [
        (home / ".claude", "CLAUDE.md"),
        (home / ".gemini", "AGENTS.md"),
        (home / ".qwen", "QWEN.md"),
        (home / ".codex", "AGENTS.md"),
        (home / ".iflow", "IFLOW.md"),
    ]

    if agents_md_source.exists():
        for root_dir, target_file_name in agents_md_targets:
            if root_dir.exists():
                link_path = root_dir / target_file_name
                if not link_path.exists() and not link_path.is_symlink():
                    safe_symlink(agents_md_source, link_path)
                else:
                    print(f"  Skipping AGENTS.md link to {root_dir.name}/{target_file_name}: already exists.")
            else:
                print(f"Skipping {root_dir.name}: directory does not exist for AGENTS.md symlink.")

        # Handle Roo AGENTS.md symlink to ~/.roo/rules/AGENTS.md
        target_roo_rules = home / ".roo" / "rules"
        if target_roo_root.exists():
            target_roo_rules.mkdir(parents=True, exist_ok=True)
            link_path = target_roo_rules / "AGENTS.md"
            if not link_path.exists() and not link_path.is_symlink():
                safe_symlink(agents_md_source, link_path)
            else:
                print(f"  Skipping AGENTS.md link to .roo/rules/AGENTS.md: already exists.")
        else:
            print("Skipping .roo: directory does not exist for AGENTS.md symlink.")
    else:
        print(f"Warning: Source file '{agents_md_source}' not found. Removing existing AGENTS.md symlinks...")
        # Remove existing AGENTS.md symlinks if source file doesn't exist
        for root_dir, target_file_name in agents_md_targets:
            if root_dir.exists():
                link_path = root_dir / target_file_name
                if link_path.exists() or link_path.is_symlink():
                    safe_remove(link_path)

        # Remove Roo AGENTS.md symlink if it exists
        target_roo_rules = home / ".roo" / "rules"
        if target_roo_root.exists():
            link_path = target_roo_rules / "AGENTS.md"
            if link_path.exists() or link_path.is_symlink():
                safe_remove(link_path)

if __name__ == "__main__":
    main()