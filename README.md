# Coding Agent Configuration

This repository serves as a centralized source of truth for coding agent configurations, workflows, and custom commands. It is designed to maintain consistency across different AI coding assistants (Claude, Gemini, Qwen, Roo, Codex, iFlow, OpenCode, etc.) by synchronizing a master `AGENTS.md` and a set of custom commands.

## Structure

- **`AGENTS.md`**: The core system instruction file. It defines:
    - General and specific workflows (ARCHITECT, DEBUG, CODE).
    - Code quality principles (DRY, KISS, SOLID).
    - Formatting, naming, and security guidelines.
    - Documentation standards.
- **`Useful_Skills.md`**: Documentation for useful external skills and tools that can enhance AI coding assistant capabilities.
- **`commands/`**: A directory containing custom commands defined in TOML format:
    - `architect.toml`: ARCHITECT a complete system architecture and implementation plan
    - `claude_agent_implement.toml`: (Claude-only) Implement tasks with baseline reproduction and validation
    - `debug.toml`: DEBUG software bugs
    - `deep_dive.toml`: Deep dive into issues by inspecting relevant files
    - `edge_case.toml`: Generate product & technical edge cases
    - `git_commit.toml`: Generate Conventional Commits formatted messages
    - `implement.toml`: IMPLEMENT code changes safely from clarified requirements with verification
    - `issue_tracker.toml`: Maintain issue tracker JSON file in doc/docs folder
    - `review_changes.toml`: Review changed files for bugs and issues
    - `start_task.toml`: Prepare before starting to make sure git is clean
    - `update_doc.toml`: Update documentation based on code changes
    - Each `.toml` file defines a command with a `description` and a `prompt`.
- **`agents/`**: Custom agent definitions for Claude Code:
    - `code-reviewer.md`: Specialized agent for reviewing code quality
    - `docs-updater.md`: Agent for keeping documentation accurate
- **`mcp.json`**: Configuration file for Model Context Protocol (MCP) servers, including:
    - `context7`: HTTP-based MCP server for retrieving up-to-date library documentation
    - `figma-desktop`: Figma desktop integration via local HTTP endpoint
    - `playwright`: Browser automation and testing capabilities (via npx)
    - `chrome-devtools`: Chrome DevTools integration for debugging (via npx)
- **`sync_commands.py`**: A utility script to deploy these configurations to the respective agent directories in your home folder.
- **`play_notification.py`**: Cross-platform script to play audio notifications.
- **`tests/`**: Unit tests for sync_commands.py functionality.
- **`positive-notification.wav`**: Audio file for notification playback.

## Synchronization Script (`sync_commands.py`)

The `sync_commands.py` script automates the distribution of configs to supported agent directories (e.g., `~/.gemini`, `~/.claude`, `~/.qwen`).

### What it does:

1.  **Commands Distribution**:
    - **Gemini, Qwen, iFlow**: Symlinks `.toml` files from `commands/` to `~/.<agent>/commands/`.
    - **Claude**: Extracts the `prompt` and `description` from `.toml` files and saves them as Markdown files with YAML front matter in `~/.claude/commands/`. Includes `disable-model-invocation: true` field. Commands prefixed with `claude_` (e.g., `claude_agent_implement.toml`) are Claude-only and have the prefix stripped in the output (e.g., `agent_implement.md`).
    - **Roo, Codex**: Extracts prompts and descriptions to `.md` files with YAML front matter for shared commands only (non-`claude_` prefixed).
    - **OpenCode**: Extracts prompts and descriptions to `.md` files with YAML front matter in `~/.config/opencode/command/`. All commands (including `claude_` prefixed) are synced with the prefix stripped.
    - **Command Filtering**: Files starting with `claude_` are distributed only to Claude tools (except OpenCode, which receives all commands with prefix stripped). All other commands are shared across all tools.
    - **File Regeneration**: All `.md` command files are fully regenerated on each run. Files that match a source `.toml` but were not recreated in the current run are considered stale and removed. This ensures consistency and prevents orphaned files from accumulating.
    - **Cleanup**: Automatically removes stale symlinks and `.md` files when source `.toml` files are deleted.

2.  **Agents Folder Distribution**:
    - **Claude**: Symlinks `.md` files from `./agents/` to `~/.claude/agents/` for Claude Code's agent system.
    - **OpenCode**: Extracts `description` field from agent frontmatter and adds `mode: subagent` field, writing to `~/.config/opencode/agent/`.
    - Supports custom agent definitions that can be referenced in command prompts.

3.  **`AGENTS.md` Distribution**:
    - Symlinks the root `AGENTS.md` to the appropriate location and filename for each agent:
        - `~/.claude/CLAUDE.md`
        - `~/.gemini/AGENTS.md`
        - `~/.qwen/QWEN.md`
        - `~/.codex/AGENTS.md`
        - `~/.iflow/IFLOW.md`
        - `~/.roo/rules/AGENTS.md`
        - `~/.config/opencode/AGENTS.md`
    - **Cleanup**: Removes symlinks if the source `AGENTS.md` file is deleted.

### Prerequisites

- Python 3.x
- `tomli` package (required for Python < 3.11)
- `pyyaml` package (optional, recommended for proper YAML escaping with multi-line descriptions)

```bash
pip install tomli pyyaml
```

**Note:** `pyyaml` is optional but recommended. The script will function without it by using a fallback escaping method, but multi-line descriptions in command files will have newlines replaced with spaces if PyYAML is not installed.

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

## Running Tests

Unit tests are provided to verify the functionality of `sync_commands.py`, including YAML front matter generation, symlink validation, and cleanup operations.

```bash
# Run all tests
python3 -m pytest tests/

# Run with verbose output
python3 -m pytest tests/ -v

# Run specific test class
python3 -m pytest tests/test_sync_commands.py::TestFormatYamlDict -v

# Run using unittest directly
python3 -m unittest tests.test_sync_commands
```

## Audio Notifications

The `play_notification.py` script plays the `positive-notification.wav` audio file. It works from any directory and supports:

- **Windows**: Built-in `winsound` module
- **macOS/Linux**: Requires `simpleaudio` or `pygame`

```bash
# Install audio playback library (macOS/Linux)
pip install simpleaudio

# Play the notification sound
python3 play_notification.py
```
