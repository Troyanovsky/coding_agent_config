# Coding Agent Configuration

This repository serves as a centralized source of truth for coding agent configurations, workflows, and custom commands. It is designed to maintain consistency across different AI coding assistants (Gemini, Qwen, Claude, iFlow, etc.) by synchronizing a master `AGENTS.md` and a set of custom commands.

## Structure

- **`AGENTS.md`**: The core system instruction file. It defines:
    - General and specific workflows (ARCHITECT, DEBUG, CODE).
    - Code quality principles (DRY, KISS, SOLID).
    - Formatting, naming, and security guidelines.
    - Documentation standards.
- **`commands/`**: A directory containing custom commands defined in TOML format:
    - `architect.toml`: ARCHITECT a complete system architecture and implementation plan
    - `debug.toml`: DEBUG software bugs
    - `deep_dive.toml`: Deep dive into issues by inspecting relevant files
    - `edge_case.toml`: Generate product & technical edge cases
    - `git_commit.toml`: Generate Conventional Commits formatted messages
    - `implement.toml`: IMPLEMENT code changes safely from clarified requirements with verification
    - `review_changes.toml`: Review changed files for bugs and issues
    - `start_task.toml`: Prepare before starting to make sure git is clean
    - `update_doc.toml`: Update documentation based on code changes
    - Each `.toml` file defines a command with a `description` and a `prompt`.
- **`mcp.json`**: Configuration file for Model Context Protocol (MCP) servers, including:
    - `context7`: HTTP-based MCP server for context management
    - `figma-desktop`: Figma desktop integration via local HTTP endpoint
    - `playwright`: Browser automation and testing capabilities
    - `chrome-devtools`: Chrome DevTools integration for debugging
- **`sync_commands.py`**: A utility script to deploy these configurations to the respective agent directories in your home folder.

## Synchronization Script (`sync_commands.py`)

The `sync_commands.py` script automates the distribution of configs to supported agent directories (e.g., `~/.gemini`, `~/.claude`, `~/.qwen`).

### What it does:

1.  **Commands Distribution**:
    - **Gemini, Qwen, iFlow**: Symlinks `.toml` files from `commands/` to `~/.<agent>/commands/`.
    - **Claude & Roo**: Extracts the `prompt` string from `.toml` files and saves them as Markdown files in `~/.claude/commands/` and `~/.roo/commands/` (since these tools typically use `.md` files for prompts).
    - Supports all 9 command files: architect, debug, deep_dive, edge_case, git_commit, implement, review_changes, start_task, and update_doc.
    - **Cleanup**: Automatically removes stale symlinks and `.md` files when source `.toml` files are deleted.

2.  **`AGENTS.md` Distribution**:
    - Symlinks the root `AGENTS.md` to the appropriate location and filename for each agent:
        - `~/.claude/CLAUDE.md`
        - `~/.gemini/AGENTS.md`
        - `~/.qwen/QWEN.md`
        - `~/.codex/AGENTS.md`
        - `~/.iflow/IFLOW.md`
        - `~/.roo/rules/AGENTS.md`
    - **Cleanup**: Removes symlinks if the source `AGENTS.md` file is deleted.

### Prerequisites

- Python 3.x
- `tomli` package (required for Python < 3.11)

```bash
pip install tomli
```

### Usage

Run the script from the repository root:

```bash
python3 sync_commands.py
```

The script will:
- Check for existing directories in your home folder.
- Create necessary subdirectories (e.g., `commands/`).
- Create symlinks for `AGENTS.md` and command files.
- Generate Markdown command files for Claude.
- Report success or errors (e.g., missing permissions on Windows).

## Adding New Commands

1.  Create a new `.toml` file in the `commands/` directory.
2.  Use the following format:

```toml
description = "Brief description of what the command does."
prompt = """
Detailed instructions for the agent.
1. Step one
2. Step two
...
"""
```

3.  Run `python3 sync_commands.py` to apply the changes.
