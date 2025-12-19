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

def expand_path(path_str):
    return pathlib.Path(path_str).expanduser().resolve()

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
            
            for source_file in toml_files:
                link_name = cmd_dir / source_file.name
                
                # Check if link/file already exists
                if link_name.exists() or link_name.is_symlink():
                    print(f"  Skipping {source_file.name}: symlink already exists in {cmd_dir.name}")
                    continue
                
                # Create symlink (absolute path for safety)
                safe_symlink(source_file.resolve(), link_name)
        else:
            print(f"Skipping {root_dir.name}: directory does not exist.")

    # 2. Handle Claude (Extraction)
    if target_claude_root.exists():
        print(f"Processing .claude...")
        target_claude_cmds.mkdir(parents=True, exist_ok=True)
        
        for source_file in toml_files:
            try:
                with open(source_file, "rb") as f:
                    data = tomllib.load(f)
                
                if "prompt" in data:
                    prompt_content = data["prompt"]
                    # Create .md filename
                    md_filename = source_file.stem + ".md"
                    target_file = target_claude_cmds / md_filename
                    
                    # Write extracted prompt
                    with open(target_file, "w", encoding="utf-8") as f:
                        f.write(prompt_content)
                        
                    print(f"  Extracted prompt from {source_file.name} -> .claude/commands/{md_filename}")
                else:
                    print(f"  Skipping {source_file.name}: no 'prompt' key.")
            except Exception as e:
                print(f"  Error processing {source_file.name} for Claude: {e}")
    else:
        print("Skipping .claude: directory does not exist.")

    # 3. Handle AGENTS.md Symlinks
    agents_md_source = pathlib.Path("AGENTS.md").resolve()
    if not agents_md_source.exists():
        print(f"Error: Source file '{agents_md_source}' not found. Cannot create AGENTS.md symlinks.")
        return

    print(f"\nProcessing AGENTS.md symlinks...")

    # Define target configurations for AGENTS.md
    agents_md_targets = [
        (home / ".claude", "CLAUDE.md"),
        (home / ".gemini", "AGENTS.md"),
        (home / ".qwen", "QWEN.md"),
        (home / ".codex", "AGENTS.md"),
        (home / ".iflow", "IFLOW.md"),
    ]

    for root_dir, target_file_name in agents_md_targets:
        if root_dir.exists():
            link_path = root_dir / target_file_name
            if not link_path.exists() and not link_path.is_symlink():
                safe_symlink(agents_md_source, link_path)
            else:
                print(f"  Skipping AGENTS.md link to {root_dir.name}/{target_file_name}: already exists.")
        else:
            print(f"Skipping {root_dir.name}: directory does not exist for AGENTS.md symlink.")

if __name__ == "__main__":
    main()
