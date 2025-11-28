# Coding Agent Configuration

This repository serves as a centralized source of truth for coding agent configurations, workflows, and custom commands. It is designed to maintain consistency across different AI coding assistants (Gemini, Qwen, Claude, etc.) by synchronizing a master `AGENTS.md` and a set of custom commands.

## Structure

- **`AGENTS.md`**: The core system instruction file. It defines:
    - General and specific workflows (ARCHITECT, DEBUG, CODE).
    - Code quality principles (DRY, KISS, SOLID).
    - Formatting, naming, and security guidelines.
    - Documentation standards.
- **`commands/`**: A directory containing custom commands defined in TOML format.
    - Each `.toml` file (e.g., `deep_dive.toml`) defines a command with a `description` and a `prompt`.
- **`sync_commands.py`**: A utility script to deploy these configurations to the respective agent directories in your home folder.

## Synchronization Script (`sync_commands.py`)

The `sync_commands.py` script automates the distribution of configs to supported agent directories (e.g., `~/.gemini`, `~/.claude`, `~/.qwen`).

### What it does:

1.  **Commands Distribution**:
    - **Gemini & Qwen**: Symlinks `.toml` files from `commands/` to `~/.<agent>/commands/`.
    - **Claude**: Extracts the `prompt` string from `.toml` files and saves them as Markdown files in `~/.claude/commands/` (since Claude typically uses `.md` files for prompts).

2.  **`AGENTS.md` Distribution**:
    - Symlinks the root `AGENTS.md` to the appropriate location and filename for each agent:
        - `~/.claude/CLAUDE.md`
        - `~/.gemini/AGENTS.md`
        - `~/.qwen/QWEN.md`
        - `~/.codex/AGENTS.md`
        - `~/.iflow/IFLOW.md`

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
