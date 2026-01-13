"""
Unit tests for sync_commands.py module.

Tests the YAML front matter generation functionality including proper
escaping of multi-line strings, special YAML characters, and Unicode.
"""

import os
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

# Add parent directory to path to import sync_commands
sys.path.insert(0, str(Path(__file__).parent.parent))

import sync_commands


class TestEscapeYamlString(unittest.TestCase):
    """Test the _escape_yaml_string helper function."""

    def test_simple_string(self):
        """Simple strings should remain unchanged."""
        result = sync_commands._escape_yaml_string("Hello world")
        self.assertEqual(result, "Hello world")

    def test_single_quote(self):
        """Single quotes should be doubled (YAML escaping rule)."""
        result = sync_commands._escape_yaml_string("It's great")
        self.assertEqual(result, "It''s great")

    def test_multiple_single_quotes(self):
        """Multiple single quotes should all be doubled."""
        result = sync_commands._escape_yaml_string("'quoted' text")
        self.assertEqual(result, "''quoted'' text")

    def test_backslash(self):
        """Backslashes should remain unchanged in YAML single-quoted style."""
        result = sync_commands._escape_yaml_string(r"path\to\file")
        self.assertEqual(result, r"path\to\file")

    def test_combined_quotes_and_backslashes(self):
        """Only quotes should be escaped; backslashes remain unchanged."""
        result = sync_commands._escape_yaml_string(r"It's a \path")
        self.assertEqual(result, r"It''s a \path")


class TestFormatYamlDict(unittest.TestCase):
    """Test the _format_yaml_dict function."""

    def test_simple_description(self):
        """Simple descriptions should format correctly."""
        result = sync_commands._format_yaml_dict({"description": "A simple description"})
        # With PyYAML: "description: A simple description" (no quotes)
        # Without PyYAML: "description: 'A simple description'"
        self.assertIn("description:", result)
        self.assertIn("A simple description", result)

    def test_special_yaml_characters(self):
        """Special YAML characters should be properly escaped."""
        result = sync_commands._format_yaml_dict({"description": "Use colons: and [brackets]"})
        # Should be valid YAML - no unescaped special chars
        self.assertIn("description:", result)

    def test_colon_character(self):
        """Colons should not break YAML formatting."""
        result = sync_commands._format_yaml_dict({"description": "Step 1: Do something"})
        self.assertIn("description:", result)

    def test_brackets(self):
        """Brackets should be properly handled."""
        result = sync_commands._format_yaml_dict({"description": "See [documentation](link)"})
        self.assertIn("description:", result)

    def test_braces(self):
        """Braces should be properly handled."""
        result = sync_commands._format_yaml_dict({"description": "Use {key: value}"})
        self.assertIn("description:", result)

    def test_unicode_characters(self):
        """Unicode characters should be preserved."""
        result = sync_commands._format_yaml_dict({"description": "Unicode: café, 日本語, emoji 🎉"})
        self.assertIn("description:", result)
        # Unicode should be present, not escaped
        self.assertIn("café", result)

    def test_quotes_in_description(self):
        """Quotes should be properly escaped."""
        result = sync_commands._format_yaml_dict({"description": 'He said "hello"'})
        self.assertIn("description:", result)

    def test_empty_string(self):
        """Empty strings should be handled."""
        result = sync_commands._format_yaml_dict({"description": ""})
        self.assertIn("description:", result)

    def test_extra_boolean_field(self):
        """Extra fields like booleans should be properly formatted."""
        result = sync_commands._format_yaml_dict({"description": "Test", "disable-model-invocation": True})
        self.assertIn("description:", result)
        self.assertIn("disable-model-invocation:", result)
        self.assertIn("true", result)  # YAML uses lowercase boolean literals


class TestFormatYamlDictWithoutPyYaml(unittest.TestCase):
    """Test _format_yaml_dict behavior without PyYAML."""

    def setUp(self):
        self.original_has_yaml = sync_commands.HAS_YAML
        sync_commands.HAS_YAML = False

    def tearDown(self):
        sync_commands.HAS_YAML = self.original_has_yaml

    def test_multiline_description_replaces_newlines(self):
        """Multi-line descriptions are flattened when PyYAML is unavailable."""
        result = sync_commands._format_yaml_dict({"description": "Line one\nLine two"})
        self.assertIn("description:", result)
        self.assertNotIn("\n", result)
        self.assertIn("Line one Line two", result)


class TestGetOutputStem(unittest.TestCase):
    """Test the _get_output_stem helper function."""

    def test_no_strip_prefix(self):
        """When no prefix is provided, the stem is unchanged."""
        result = sync_commands._get_output_stem("example", None)
        self.assertEqual(result, "example")

    def test_strip_prefix(self):
        """A matching prefix should be stripped."""
        result = sync_commands._get_output_stem("claude_command", "claude_")
        self.assertEqual(result, "command")

    def test_strip_prefix_empty_string(self):
        """Empty prefix should behave like None."""
        result = sync_commands._get_output_stem("example", "")
        self.assertEqual(result, "example")

    def test_strip_prefix_to_empty_returns_none(self):
        """If stripping removes the full stem, return None."""
        result = sync_commands._get_output_stem("claude_", "claude_")
        self.assertIsNone(result)


class TestWritePromptFile(unittest.TestCase):
    """Test the _write_prompt_file function."""

    def setUp(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.test_dir)

    def test_write_without_description(self):
        """Files without description should have no YAML front matter."""
        test_file = Path(self.test_dir) / "test.md"
        content = "# Test Prompt\n\nThis is a test."

        sync_commands._write_prompt_file(test_file, content, None)

        with open(test_file, "r", encoding="utf-8") as f:
            result = f.read()

        self.assertEqual(result, content)
        self.assertNotIn("---", result)

    def test_write_with_simple_description(self):
        """Files with description should have YAML front matter."""
        test_file = Path(self.test_dir) / "test.md"
        content = "# Test Prompt\n\nThis is a test."
        description = "A simple description"

        sync_commands._write_prompt_file(test_file, content, description)

        with open(test_file, "r", encoding="utf-8") as f:
            result = f.read()

        self.assertIn("---", result)
        self.assertIn("description:", result)
        self.assertIn(description, result)
        self.assertIn(content, result)

    def test_write_with_special_characters(self):
        """Descriptions with special YAML chars should produce valid YAML."""
        test_file = Path(self.test_dir) / "test.md"
        content = "# Test"
        description = "Use : [] {} ! & * characters"

        sync_commands._write_prompt_file(test_file, content, description)

        with open(test_file, "r", encoding="utf-8") as f:
            result = f.read()

        # Should have proper YAML structure
        self.assertIn("---\n", result)
        self.assertIn("\n---\n\n", result)

    def test_write_with_unicode(self):
        """Unicode characters should be preserved in output."""
        test_file = Path(self.test_dir) / "test.md"
        content = "# Test"
        description = "Café, 日本語, 🎉"

        sync_commands._write_prompt_file(test_file, content, description)

        with open(test_file, "r", encoding="utf-8") as f:
            result = f.read()

        self.assertIn("Café", result)
        self.assertIn("日本語", result)
        self.assertIn("🎉", result)

    def test_write_with_quotes(self):
        """Quotes should be properly escaped."""
        test_file = Path(self.test_dir) / "test.md"
        content = "# Test"
        description = 'He said "hello" and \'goodbye\''

        sync_commands._write_prompt_file(test_file, content, description)

        with open(test_file, "r", encoding="utf-8") as f:
            result = f.read()

        # Should be valid YAML (no parsing errors)
        self.assertIn("---", result)
        self.assertIn("description:", result)

    def test_write_no_duplicate_yaml_markers(self):
        """PyYAML output should not create duplicate --- markers."""
        test_file = Path(self.test_dir) / "test.md"
        content = "# Test"
        description = "A description"

        sync_commands._write_prompt_file(test_file, content, description)

        with open(test_file, "r", encoding="utf-8") as f:
            result = f.read()

        # Should start with single --- delimiter, not duplicated
        self.assertTrue(result.startswith("---\n"))
        # Should not have --- immediately followed by another ---
        self.assertNotIn("---\n---", result)
        # Should have proper YAML front matter structure
        self.assertIn("\n---\n\n", result)


class TestSymlinkValidation(unittest.TestCase):
    """Test symlink target verification and replacement logic."""

    def setUp(self):
        """Create temporary directories and files for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = Path(self.test_dir) / "source"
        self.target_dir = Path(self.test_dir) / "target"
        self.source_dir.mkdir()
        self.target_dir.mkdir()

        # Create test source files
        self.file1 = self.source_dir / "test1.txt"
        self.file2 = self.source_dir / "test2.txt"
        self.file1.write_text("content1")
        self.file2.write_text("content2")

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.test_dir)

    def test_correct_symlink_is_skipped(self):
        """Existing symlinks pointing to correct targets should be skipped."""
        source_files = [self.file1]
        link_name = self.target_dir / "test1.txt"

        # Create correct symlink
        os.symlink(self.file1, link_name)

        # Sync should skip existing correct symlink
        sync_commands._sync_symlinks_to_dir(source_files, self.target_dir, self.source_dir.resolve())

        # Verify symlink still points to correct target
        self.assertTrue(link_name.is_symlink())
        self.assertTrue(os.path.samefile(link_name.resolve(), self.file1))

    def test_incorrect_symlink_is_replaced(self):
        """Symlinks pointing to wrong targets should be replaced."""
        source_files = [self.file1]
        link_name = self.target_dir / "test1.txt"

        # Create incorrect symlink pointing to file2
        os.symlink(self.file2, link_name)

        # Sync should replace incorrect symlink
        sync_commands._sync_symlinks_to_dir(source_files, self.target_dir, self.source_dir.resolve())

        # Verify symlink now points to correct target
        self.assertTrue(link_name.is_symlink())
        self.assertTrue(os.path.samefile(link_name.resolve(), self.file1))

    def test_broken_symlink_is_replaced(self):
        """Broken symlinks should be replaced with correct ones."""
        source_files = [self.file1]
        link_name = self.target_dir / "test1.txt"

        # Create broken symlink pointing to non-existent file
        nonexistent = self.source_dir / "nonexistent.txt"
        os.symlink(nonexistent, link_name)

        # Sync should replace broken symlink
        sync_commands._sync_symlinks_to_dir(source_files, self.target_dir, self.source_dir.resolve())

        # Verify symlink now points to correct target
        self.assertTrue(link_name.is_symlink())
        self.assertTrue(os.path.samefile(link_name.resolve(), self.file1))

    def test_regular_file_is_replaced(self):
        """Regular files (not symlinks) should be replaced with symlinks."""
        source_files = [self.file1]
        link_name = self.target_dir / "test1.txt"

        # Create regular file with different content
        link_name.write_text("wrong content")

        # Sync should replace regular file with symlink
        sync_commands._sync_symlinks_to_dir(source_files, self.target_dir, self.source_dir.resolve())

        # Verify it's now a symlink pointing to correct target
        self.assertTrue(link_name.is_symlink())
        self.assertTrue(os.path.samefile(link_name.resolve(), self.file1))

    def test_multiple_symlinks_mixed_states(self):
        """Handle multiple symlinks with different states correctly."""
        source_files = [self.file1, self.file2]

        # Create correct symlink for file1
        link1 = self.target_dir / "test1.txt"
        os.symlink(self.file1, link1)

        # Create incorrect symlink for file2 (points to file1)
        link2 = self.target_dir / "test2.txt"
        os.symlink(self.file1, link2)

        # Sync should handle both correctly
        sync_commands._sync_symlinks_to_dir(source_files, self.target_dir, self.source_dir.resolve())

        # Verify both symlinks are correct
        self.assertTrue(os.path.samefile(link1.resolve(), self.file1))
        self.assertTrue(os.path.samefile(link2.resolve(), self.file2))


class TestCleanupHelpers(unittest.TestCase):
    """Test cleanup helpers for .md files and symlinks."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.target_dir = Path(self.test_dir) / "target"
        self.target_dir.mkdir()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_should_remove_md_file_keeps_recent_output(self):
        """Freshly created .md files should be kept."""
        toml_files = [Path("command.toml")]
        created = {"command.md"}
        md_file = Path("command.md")
        result = sync_commands._should_remove_md_file(md_file, toml_files, created, None)
        self.assertFalse(result)

    def test_should_remove_md_file_removes_stale_output(self):
        """Stale .md files should be removed."""
        toml_files = [Path("command.toml")]
        created = set()
        md_file = Path("command.md")
        result = sync_commands._should_remove_md_file(md_file, toml_files, created, None)
        self.assertTrue(result)

    def test_should_remove_md_file_removes_old_prefix_format(self):
        """Old format (unstripped) names should be removed when prefix is used."""
        toml_files = [Path("claude_command.toml")]
        created = {"command.md"}
        md_file = Path("claude_command.md")
        result = sync_commands._should_remove_md_file(md_file, toml_files, created, "claude_")
        self.assertTrue(result)

    def test_cleanup_stale_md_files(self):
        """Cleanup removes stale .md files while keeping fresh ones."""
        toml_files = [Path("keep.toml"), Path("remove.toml")]
        created = {"keep.md"}
        keep_file = self.target_dir / "keep.md"
        remove_file = self.target_dir / "remove.md"
        orphan_file = self.target_dir / "orphan.md"
        keep_file.write_text("keep")
        remove_file.write_text("remove")
        orphan_file.write_text("orphan")

        sync_commands._cleanup_stale_md_files(self.target_dir, toml_files, created, None)

        self.assertTrue(keep_file.exists())
        self.assertFalse(remove_file.exists())
        self.assertFalse(orphan_file.exists())

    def test_cleanup_stale_symlinks(self):
        """Cleanup removes symlinks pointing to missing source files."""
        source_dir = Path(self.test_dir) / "source"
        source_dir.mkdir()
        source_file = source_dir / "keep.txt"
        source_file.write_text("content")
        other_dir = Path(self.test_dir) / "other"
        other_dir.mkdir()
        other_file = other_dir / "other.txt"
        other_file.write_text("content")

        kept_link = self.target_dir / "keep.txt"
        stale_link = self.target_dir / "stale.txt"
        external_link = self.target_dir / "external.txt"
        os.symlink(source_file, kept_link)
        os.symlink(source_dir / "missing.txt", stale_link)
        os.symlink(other_file, external_link)

        sync_commands._cleanup_stale_symlinks(self.target_dir, [source_file], source_dir.resolve())

        self.assertTrue(kept_link.exists())
        self.assertFalse(stale_link.exists())
        self.assertTrue(external_link.exists())


class TestSymlinkTargets(unittest.TestCase):
    """Test syncing symlinks to target directories."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = Path(self.test_dir) / "source"
        self.source_dir.mkdir()
        self.root_dir = Path(self.test_dir) / "root"
        self.root_dir.mkdir()
        self.cmd_dir = self.root_dir / "commands"
        self.cmd_dir.mkdir()
        self.source_file = self.source_dir / "command.toml"
        self.source_file.write_text("prompt = \"hi\"")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_sync_symlink_targets_creates_links(self):
        """Symlinks should be created in existing target directories."""
        sync_commands._sync_symlink_targets(
            [self.source_file],
            self.source_dir,
            [(self.root_dir, self.cmd_dir)],
        )

        link_path = self.cmd_dir / self.source_file.name
        self.assertTrue(link_path.is_symlink())
        self.assertTrue(os.path.samefile(link_path.resolve(), self.source_file))


class TestProcessSourceFile(unittest.TestCase):
    """Test _process_source_file behavior."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = Path(self.test_dir) / "source"
        self.target_dir = Path(self.test_dir) / "target"
        self.source_dir.mkdir()
        self.target_dir.mkdir()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_process_source_file_writes_prompt(self):
        """Prompt content should be written to a .md file."""
        source_file = self.source_dir / "command.toml"
        source_file.write_text('prompt = "Hello"\n')

        result = sync_commands._process_source_file(
            source_file,
            self.target_dir,
            "tool",
            strip_prefix=None,
            include_description=False,
        )

        self.assertEqual(result, "command.md")
        target_file = self.target_dir / "command.md"
        self.assertTrue(target_file.exists())
        self.assertEqual(target_file.read_text(encoding="utf-8"), "Hello")

    def test_process_source_file_missing_prompt(self):
        """Files without prompt should be skipped."""
        source_file = self.source_dir / "missing.toml"
        source_file.write_text('description = "No prompt"\n')

        result = sync_commands._process_source_file(
            source_file,
            self.target_dir,
            "tool",
            strip_prefix=None,
            include_description=False,
        )

        self.assertIsNone(result)
        self.assertFalse((self.target_dir / "missing.md").exists())


class TestParseYamlFrontmatter(unittest.TestCase):
    """Test the _parse_yaml_frontmatter helper function."""

    def test_no_frontmatter(self):
        """Content without frontmatter delimiters should return None and original content."""
        content = "# Title\n\nSome content"
        frontmatter, body = sync_commands._parse_yaml_frontmatter(content)
        self.assertIsNone(frontmatter)
        self.assertEqual(body, content)

    def test_valid_frontmatter(self):
        """Valid frontmatter should be parsed correctly."""
        content = "---\nname: test\ndescription: A test\n---\n\nBody content"
        frontmatter, body = sync_commands._parse_yaml_frontmatter(content)
        self.assertIsNotNone(frontmatter)
        self.assertEqual(frontmatter.get("name"), "test")
        self.assertEqual(frontmatter.get("description"), "A test")
        self.assertEqual(body, "\nBody content")

    def test_missing_end_delimiter(self):
        """Content with start delimiter but no end delimiter should return None."""
        content = "---\nname: test\n\nBody content"
        frontmatter, body = sync_commands._parse_yaml_frontmatter(content)
        self.assertIsNone(frontmatter)
        self.assertEqual(body, content)

    def test_empty_frontmatter(self):
        """Empty frontmatter dict should return None."""
        content = "---\n---\n\nBody content"
        frontmatter, body = sync_commands._parse_yaml_frontmatter(content)
        # Empty dict may be returned as None depending on yaml.safe_load
        self.assertIn(frontmatter, [None, {}])
        self.assertEqual(body, "\nBody content")


class TestOpenCodeAgentSync(unittest.TestCase):
    """Test OpenCode agent synchronization."""

    def setUp(self):
        """Create temporary directories and save original agents directory."""
        self.test_dir = tempfile.mkdtemp()
        self.target_dir = Path(self.test_dir) / "opencode_agent"
        self.target_dir.mkdir(parents=True)

        # Save original agents directory if it exists
        self.original_agents = Path("./agents").resolve()
        self.backup_agents = None
        if self.original_agents.exists():
            # Create a backup
            self.backup_agents = Path(self.test_dir) / "backup_agents"
            import shutil
            shutil.copytree(self.original_agents, self.backup_agents)

        # Create temporary agents directory for testing
        self.test_agents_dir = Path("./agents").resolve()
        if self.test_agents_dir.exists():
            import shutil
            shutil.rmtree(self.test_agents_dir)
        self.test_agents_dir.mkdir()

    def tearDown(self):
        """Clean up temporary files and restore original agents."""
        import shutil
        # Remove test agents directory
        if self.test_agents_dir.exists():
            shutil.rmtree(self.test_agents_dir)

        # Restore original agents if it was backed up
        if self.backup_agents and self.backup_agents.exists():
            shutil.copytree(self.backup_agents, self.original_agents)

        # Clean up test directory
        shutil.rmtree(self.test_dir)

    def test_agent_with_description(self):
        """Agent with description should have description and mode in frontmatter."""
        agent_file = self.test_agents_dir / "test_agent.md"
        agent_file.write_text(
            "---\n"
            "name: test-agent\n"
            "description: A test agent\n"
            "tools: Read, Write\n"
            "---\n\n"
            "You are a test agent."
        )

        sync_commands._sync_opencode_agents_folder(self.target_dir)

        target_file = self.target_dir / "test_agent.md"
        self.assertTrue(target_file.exists())

        content = target_file.read_text(encoding="utf-8")
        self.assertIn("---", content)
        self.assertIn("description: A test agent", content)
        self.assertIn("mode: subagent", content)
        # Original name and tools should NOT be in output
        self.assertNotIn("name: test-agent", content)
        self.assertNotIn("tools: Read, Write", content)
        # Body content should be preserved
        self.assertIn("You are a test agent.", content)

    def test_agent_without_frontmatter(self):
        """Agent without frontmatter should have only mode in frontmatter."""
        agent_file = self.test_agents_dir / "no_frontmatter.md"
        agent_file.write_text("You are an agent without frontmatter.")

        sync_commands._sync_opencode_agents_folder(self.target_dir)

        target_file = self.target_dir / "no_frontmatter.md"
        self.assertTrue(target_file.exists())

        content = target_file.read_text(encoding="utf-8")
        self.assertIn("mode: subagent", content)
        self.assertIn("You are an agent without frontmatter.", content)

    def test_agent_cleanup_removes_stale(self):
        """Stale agent files should be removed."""
        # Create initial agent
        agent_file = self.test_agents_dir / "active.md"
        agent_file.write_text(
            "---\n"
            "description: Active agent\n"
            "---\n\n"
            "Active content"
        )

        # Create a stale file in target that won't be recreated
        stale_file = self.target_dir / "stale.md"
        stale_file.write_text("Stale content")

        sync_commands._sync_opencode_agents_folder(self.target_dir)

        # Active file should exist
        self.assertTrue((self.target_dir / "active.md").exists())
        # Stale file should be removed
        self.assertFalse(stale_file.exists())

    def test_agent_with_empty_description(self):
        """Agent with empty description should still include mode field."""
        agent_file = self.test_agents_dir / "empty_desc.md"
        agent_file.write_text(
            "---\n"
            "description: \"\"\n"
            "---\n\n"
            "Content here"
        )

        sync_commands._sync_opencode_agents_folder(self.target_dir)

        target_file = self.target_dir / "empty_desc.md"
        self.assertTrue(target_file.exists())
        content = target_file.read_text(encoding="utf-8")
        self.assertIn("mode: subagent", content)
        self.assertIn("description:", content)  # Empty description still present

    def test_agent_with_malformed_yaml(self):
        """Agent with malformed YAML should fall back to no frontmatter."""
        agent_file = self.test_agents_dir / "malformed.md"
        agent_file.write_text(
            "---\n"
            "description: [unclosed bracket\n"
            "---\n\n"
            "Content"
        )

        sync_commands._sync_opencode_agents_folder(self.target_dir)

        target_file = self.target_dir / "malformed.md"
        self.assertTrue(target_file.exists())
        content = target_file.read_text(encoding="utf-8")
        # Should have mode added but no description
        self.assertIn("mode: subagent", content)
        self.assertIn("Content", content)


class TestComputeExpectedMdStems(unittest.TestCase):
    """Test the _compute_expected_md_stems helper function."""

    def test_no_prefix_stripping(self):
        """When strip_prefix is None, stems remain unchanged."""
        toml_files = [Path("command.toml"), Path("test.toml")]
        expected, old_format = sync_commands._compute_expected_md_stems(toml_files, None)
        self.assertEqual(expected, {"command", "test"})
        self.assertEqual(old_format, set())

    def test_with_prefix_stripping(self):
        """Prefix should be stripped from all matching files."""
        toml_files = [Path("claude_command.toml"), Path("claude_test.toml")]
        expected, old_format = sync_commands._compute_expected_md_stems(toml_files, "claude_")
        self.assertEqual(expected, {"command", "test"})
        self.assertEqual(old_format, {"claude_command", "claude_test"})

    def test_mixed_prefix_and_non_prefix(self):
        """Mix of files with and without prefix should be handled correctly."""
        toml_files = [Path("claude_command.toml"), Path("shared.toml")]
        expected, old_format = sync_commands._compute_expected_md_stems(toml_files, "claude_")
        self.assertEqual(expected, {"command", "shared"})
        self.assertEqual(old_format, {"claude_command"})

    def test_prefix_stripping_to_empty(self):
        """Files that become empty after stripping should be handled."""
        toml_files = [Path("claude_.toml"), Path("command.toml")]
        expected, old_format = sync_commands._compute_expected_md_stems(toml_files, "claude_")
        # When stem would be empty after stripping, the original stem is used
        self.assertEqual(expected, {"claude_", "command"})
        # The original stem is not tracked as old format since it's still used
        self.assertEqual(old_format, set())

    def test_empty_file_list(self):
        """Empty file list should return empty sets."""
        toml_files = []
        expected, old_format = sync_commands._compute_expected_md_stems(toml_files, None)
        self.assertEqual(expected, set())
        self.assertEqual(old_format, set())

    def test_multiple_files_same_stem_after_strip(self):
        """Duplicate stems after stripping should be handled."""
        toml_files = [Path("claude_test.toml"), Path("test.toml")]
        expected, old_format = sync_commands._compute_expected_md_stems(toml_files, "claude_")
        # Both files result in "test" stem
        self.assertEqual(expected, {"test"})
        self.assertEqual(old_format, {"claude_test"})


class TestSafeSymlink(unittest.TestCase):
    """Test the safe_symlink function."""

    def setUp(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.test_dir)

    def test_creates_symlink_successfully(self):
        """Symlink should be created successfully."""
        target = Path(self.test_dir) / "target.txt"
        link = Path(self.test_dir) / "link.txt"
        target.write_text("content")

        sync_commands.safe_symlink(target, link)

        self.assertTrue(link.is_symlink())
        self.assertTrue(os.path.samefile(link.resolve(), target))

    def test_handles_windows_permission_error(self):
        """Test Windows WinError 1314 (insufficient privileges)."""
        target = Path(self.test_dir) / "target.txt"
        link = Path(self.test_dir) / "link.txt"
        target.write_text("content")

        with unittest.mock.patch('os.symlink') as mock_symlink:
            # Create OSError with winerror attribute
            error = OSError("Privilege not held")
            error.winerror = 1314
            mock_symlink.side_effect = error

            with unittest.mock.patch('platform.system', return_value='Windows'):
                # Should not raise, should print error message
                sync_commands.safe_symlink(target, link)

            mock_symlink.assert_called_once()

    def test_handles_generic_os_error(self):
        """Generic OSError should be handled gracefully."""
        target = Path(self.test_dir) / "target.txt"
        link = Path(self.test_dir) / "link.txt"
        target.write_text("content")

        with unittest.mock.patch('os.symlink') as mock_symlink:
            mock_symlink.side_effect = OSError("Generic error")

            # Should not raise
            sync_commands.safe_symlink(target, link)

            mock_symlink.assert_called_once()


class TestSafeRemove(unittest.TestCase):
    """Test the safe_remove function."""

    def setUp(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.test_dir)

    def test_removes_regular_file(self):
        """Regular file should be removed successfully."""
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("content")

        result = sync_commands.safe_remove(test_file)

        self.assertTrue(result)
        self.assertFalse(test_file.exists())

    def test_removes_symlink(self):
        """Symlink should be removed successfully."""
        target = Path(self.test_dir) / "target.txt"
        link = Path(self.test_dir) / "link.txt"
        target.write_text("content")
        os.symlink(target, link)

        result = sync_commands.safe_remove(link)

        self.assertTrue(result)
        self.assertFalse(link.exists())
        # Target should still exist
        self.assertTrue(target.exists())

    def test_handles_nonexistent_file(self):
        """Nonexistent file should be handled gracefully."""
        test_file = Path(self.test_dir) / "nonexistent.txt"

        result = sync_commands.safe_remove(test_file)

        self.assertFalse(result)

    def test_handles_permission_error(self):
        """Permission errors should be handled gracefully."""
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("content")

        with unittest.mock.patch.object(Path, 'unlink') as mock_unlink:
            mock_unlink.side_effect = OSError("Permission denied")

            result = sync_commands.safe_remove(test_file)

            self.assertFalse(result)

    def test_returns_true_on_success(self):
        """Successful removal should return True."""
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("content")

        result = sync_commands.safe_remove(test_file)

        self.assertTrue(result)

    def test_returns_false_on_failure(self):
        """Failed removal should return False."""
        test_file = Path(self.test_dir) / "nonexistent.txt"

        result = sync_commands.safe_remove(test_file)

        self.assertFalse(result)

    def test_includes_context_in_error_message(self):
        """Context string should be included in error message."""
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("content")

        with unittest.mock.patch.object(Path, 'unlink') as mock_unlink:
            mock_unlink.side_effect = OSError("Permission denied")

            with unittest.mock.patch('builtins.print') as mock_print:
                sync_commands.safe_remove(test_file, context="test context")

                # Check that context was included in print output
                calls = [str(call) for call in mock_print.call_args_list]
                self.assertTrue(any("test context" in call for call in calls))


class TestParseYamlFrontmatterWithoutPyYaml(unittest.TestCase):
    """Test _parse_yaml_frontmatter behavior without PyYAML."""

    def setUp(self):
        """Save and disable HAS_YAML."""
        self.original_has_yaml = sync_commands.HAS_YAML
        sync_commands.HAS_YAML = False

    def tearDown(self):
        """Restore original HAS_YAML value."""
        sync_commands.HAS_YAML = self.original_has_yaml

    def test_returns_none_when_no_yaml(self):
        """Without PyYAML, frontmatter parsing should return None."""
        content = "---\nname: test\n---\n\nBody"
        frontmatter, body = sync_commands._parse_yaml_frontmatter(content)
        self.assertIsNone(frontmatter)
        # Body should be the original content
        self.assertEqual(body, content)

    def test_returns_original_content(self):
        """Content should remain unchanged when HAS_YAML=False."""
        content = "---\ndescription: Test\n---\n\nBody content"
        frontmatter, body = sync_commands._parse_yaml_frontmatter(content)
        self.assertIsNone(frontmatter)
        self.assertEqual(body, content)

    def test_prints_warning_message(self):
        """Warning message should be printed when PyYAML is not installed."""
        content = "---\nname: test\n---\n\nBody"

        with unittest.mock.patch('builtins.print') as mock_print:
            sync_commands._parse_yaml_frontmatter(content)

            # Check that warning was printed
            calls = [str(call) for call in mock_print.call_args_list]
            self.assertTrue(any("PyYAML not installed" in call for call in calls))


class TestExtractPromptsToMd(unittest.TestCase):
    """Test the extract_prompts_to_md integration function."""

    def setUp(self):
        """Create temporary directories for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = Path(self.test_dir) / "source"
        self.target_dir = Path(self.test_dir) / "target"
        self.source_dir.mkdir()
        self.target_dir.mkdir()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.test_dir)

    def test_extracts_single_file(self):
        """Single TOML file should be extracted to .md file."""
        source_file = self.source_dir / "command.toml"
        source_file.write_text('prompt = "Hello"\n')

        sync_commands.extract_prompts_to_md(
            [source_file], self.target_dir, "test_tool"
        )

        target_file = self.target_dir / "command.md"
        self.assertTrue(target_file.exists())
        self.assertEqual(target_file.read_text(encoding="utf-8"), "Hello")

    def test_extracts_multiple_files(self):
        """Multiple TOML files should be extracted."""
        file1 = self.source_dir / "command1.toml"
        file2 = self.source_dir / "command2.toml"
        file1.write_text('prompt = "Hello"\n')
        file2.write_text('prompt = "World"\n')

        sync_commands.extract_prompts_to_md(
            [file1, file2], self.target_dir, "test_tool"
        )

        self.assertTrue((self.target_dir / "command1.md").exists())
        self.assertTrue((self.target_dir / "command2.md").exists())

    def test_with_prefix_stripping(self):
        """Prefix should be stripped from output filenames."""
        source_file = self.source_dir / "claude_command.toml"
        source_file.write_text('prompt = "Test"\n')

        sync_commands.extract_prompts_to_md(
            [source_file], self.target_dir, "test_tool",
            strip_prefix="claude_"
        )

        target_file = self.target_dir / "command.md"
        self.assertTrue(target_file.exists())
        self.assertFalse((self.target_dir / "claude_command.md").exists())

    def test_with_description_included(self):
        """YAML frontmatter with description should be included."""
        source_file = self.source_dir / "command.toml"
        source_file.write_text('prompt = "Test"\ndescription = "A command"\n')

        sync_commands.extract_prompts_to_md(
            [source_file], self.target_dir, "test_tool",
            include_description=True
        )

        target_file = self.target_dir / "command.md"
        content = target_file.read_text(encoding="utf-8")
        self.assertIn("---", content)
        self.assertIn("description:", content)
        self.assertIn("A command", content)

    def test_with_extra_fields(self):
        """Extra YAML fields should be included."""
        source_file = self.source_dir / "command.toml"
        source_file.write_text('prompt = "Test"\n')

        sync_commands.extract_prompts_to_md(
            [source_file], self.target_dir, "test_tool",
            extra_fields={"disable-model-invocation": True}
        )

        target_file = self.target_dir / "command.md"
        content = target_file.read_text(encoding="utf-8")
        self.assertIn("disable-model-invocation:", content)
        self.assertIn("true", content)

    def test_cleanup_stale_files(self):
        """Orphaned .md files should be removed."""
        # Create stale file
        stale_file = self.target_dir / "stale.md"
        stale_file.write_text("old content")

        # Create new source
        source_file = self.source_dir / "command.toml"
        source_file.write_text('prompt = "Test"\n')

        sync_commands.extract_prompts_to_md(
            [source_file], self.target_dir, "test_tool"
        )

        # Stale file should be removed
        self.assertFalse(stale_file.exists())
        # New file should exist
        self.assertTrue((self.target_dir / "command.md").exists())

    def test_skips_files_without_prompt(self):
        """Files missing 'prompt' key should be skipped."""
        source_file = self.source_dir / "no_prompt.toml"
        source_file.write_text('description = "No prompt here"\n')

        sync_commands.extract_prompts_to_md(
            [source_file], self.target_dir, "test_tool"
        )

        self.assertFalse((self.target_dir / "no_prompt.md").exists())


class TestSyncAgentsFolder(unittest.TestCase):
    """Test the _sync_agents_folder function."""

    def setUp(self):
        """Create temporary directories and save original agents directory."""
        self.test_dir = tempfile.mkdtemp()
        self.target_dir = Path(self.test_dir) / "agents"
        self.target_dir.mkdir()

        # Save and backup original agents directory
        self.original_agents = Path("./agents").resolve()
        self.backup_agents = None
        if self.original_agents.exists():
            self.backup_agents = Path(self.test_dir) / "backup_agents"
            import shutil
            shutil.copytree(self.original_agents, self.backup_agents)

        # Create temporary agents directory for testing
        self.test_agents_dir = Path("./agents").resolve()
        if self.test_agents_dir.exists():
            import shutil
            shutil.rmtree(self.test_agents_dir)
        self.test_agents_dir.mkdir()

    def tearDown(self):
        """Clean up temporary files and restore original agents."""
        import shutil
        # Remove test agents directory
        if self.test_agents_dir.exists():
            shutil.rmtree(self.test_agents_dir)

        # Restore original agents if it was backed up
        if self.backup_agents and self.backup_agents.exists():
            shutil.copytree(self.backup_agents, self.original_agents)

        # Clean up test directory
        shutil.rmtree(self.test_dir)

    def test_creates_symlinks_for_agent_files(self):
        """Symlinks should be created for agent .md files."""
        # Create test agent file
        agent_file = self.test_agents_dir / "test_agent.md"
        agent_file.write_text("Agent content")

        sync_commands._sync_agents_folder(self.target_dir)

        link_path = self.target_dir / "test_agent.md"
        self.assertTrue(link_path.is_symlink())
        self.assertTrue(os.path.samefile(link_path.resolve(), agent_file))

    def test_skips_when_agents_dir_missing(self):
        """Function should skip when ./agents directory doesn't exist."""
        # Remove agents directory
        import shutil
        shutil.rmtree(self.test_agents_dir)

        # Should not raise error
        sync_commands._sync_agents_folder(self.target_dir)

        # No symlinks should be created
        self.assertEqual(list(self.target_dir.glob("*.md")), [])

    def test_skips_when_no_md_files(self):
        """Function should handle empty agents directory."""
        # Agents dir exists but no .md files
        sync_commands._sync_agents_folder(self.target_dir)

        # Should complete without error
        self.assertEqual(list(self.target_dir.glob("*.md")), [])

    def test_handles_existing_correct_symlinks(self):
        """Existing correct symlinks should be skipped."""
        agent_file = self.test_agents_dir / "test_agent.md"
        agent_file.write_text("Agent content")

        # Create existing correct symlink
        link_path = self.target_dir / "test_agent.md"
        os.symlink(agent_file, link_path)

        # Should skip existing symlink
        sync_commands._sync_agents_folder(self.target_dir)

        # Symlink should still exist and point to correct target
        self.assertTrue(link_path.is_symlink())
        self.assertTrue(os.path.samefile(link_path.resolve(), agent_file))

    def test_replaces_incorrect_symlinks(self):
        """Incorrect symlinks should be replaced."""
        agent_file = self.test_agents_dir / "test_agent.md"
        agent_file.write_text("Agent content")

        # Create incorrect symlink
        wrong_target = self.test_agents_dir / "wrong.md"
        wrong_target.write_text("Wrong")
        link_path = self.target_dir / "test_agent.md"
        os.symlink(wrong_target, link_path)

        sync_commands._sync_agents_folder(self.target_dir)

        # Symlink should now point to correct target
        self.assertTrue(os.path.samefile(link_path.resolve(), agent_file))


class TestSyncAgentsMdLinks(unittest.TestCase):
    """Test the _sync_agents_md_links and _create_agents_md_link functions."""

    def setUp(self):
        """Create temporary directories."""
        self.test_dir = tempfile.mkdtemp()
        self.home_dir = Path(self.test_dir) / "home"
        self.home_dir.mkdir()
        self.agents_md = Path(self.test_dir) / "AGENTS.md"
        self.agents_md.write_text("# Agents")

        # Save original HOME_DIR
        self.original_home = sync_commands.HOME_DIR

    def tearDown(self):
        """Clean up temporary files and restore HOME_DIR."""
        import shutil
        sync_commands.HOME_DIR = self.original_home
        shutil.rmtree(self.test_dir)

    def test_create_agents_md_link_creates_symlink(self):
        """Symlink should be created when directory exists."""
        target_dir = self.home_dir / ".claude"
        target_dir.mkdir()

        result = sync_commands._create_agents_md_link(
            self.agents_md, target_dir, "CLAUDE.md"
        )

        self.assertTrue(result)
        link_path = target_dir / "CLAUDE.md"
        self.assertTrue(link_path.is_symlink())

    def test_create_agents_md_link_skips_existing(self):
        """Existing symlink should be skipped."""
        target_dir = self.home_dir / ".claude"
        target_dir.mkdir()
        link_path = target_dir / "CLAUDE.md"
        os.symlink(self.agents_md, link_path)

        result = sync_commands._create_agents_md_link(
            self.agents_md, target_dir, "CLAUDE.md"
        )

        self.assertTrue(result)
        # Link should still exist
        self.assertTrue(link_path.exists())

    def test_create_agents_md_link_skips_missing_dir(self):
        """Function should return False when directory doesn't exist."""
        target_dir = self.home_dir / ".nonexistent"

        result = sync_commands._create_agents_md_link(
            self.agents_md, target_dir, "CLAUDE.md"
        )

        self.assertFalse(result)

    def test_sync_agents_md_links_creates_all_targets(self):
        """Links should be created to all configured targets."""
        # Create target directories
        (self.home_dir / ".claude").mkdir()
        (self.home_dir / ".gemini").mkdir()
        (self.home_dir / ".qwen").mkdir()
        (self.home_dir / ".codex").mkdir()

        with unittest.mock.patch('sync_commands.HOME_DIR', self.home_dir):
            with unittest.mock.patch('pathlib.Path.resolve', return_value=self.agents_md):
                sync_commands._sync_agents_md_links(self.home_dir)

        # Check that links were created
        self.assertTrue((self.home_dir / ".claude" / "CLAUDE.md").exists() or
                        (self.home_dir / ".claude" / "CLAUDE.md").is_symlink())
        self.assertTrue((self.home_dir / ".gemini" / "AGENTS.md").exists() or
                        (self.home_dir / ".gemini" / "AGENTS.md").is_symlink())

    def test_sync_agents_md_links_skips_when_source_missing(self):
        """Links should be removed when source AGENTS.md is missing."""
        # Create target directories with existing links
        target_dir = self.home_dir / ".claude"
        target_dir.mkdir()
        link_path = target_dir / "CLAUDE.md"
        link_path.write_text("old link")

        # Remove AGENTS.md source
        self.agents_md.unlink()

        with unittest.mock.patch('sync_commands.HOME_DIR', self.home_dir):
            with unittest.mock.patch('pathlib.Path.resolve', return_value=self.agents_md):
                sync_commands._sync_agents_md_links(self.home_dir)

        # Link should be removed
        self.assertFalse(link_path.exists())


class TestRemoveAgentsMdLink(unittest.TestCase):
    """Test the _remove_agents_md_link function."""

    def setUp(self):
        """Create temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.target_dir = Path(self.test_dir) / "target"

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.test_dir)

    def test_removes_existing_symlink(self):
        """Existing symlink should be removed."""
        self.target_dir.mkdir()
        source = Path(self.test_dir) / "source.md"
        source.write_text("content")
        link_path = self.target_dir / "CLAUDE.md"
        os.symlink(source, link_path)

        sync_commands._remove_agents_md_link(self.target_dir, "CLAUDE.md")

        self.assertFalse(link_path.exists())

    def test_skips_when_directory_missing(self):
        """Function should skip when directory doesn't exist."""
        # Should not raise error
        sync_commands._remove_agents_md_link(self.target_dir, "CLAUDE.md")

    def test_skips_when_link_missing(self):
        """Function should skip when link doesn't exist."""
        self.target_dir.mkdir()

        # Should not raise error
        sync_commands._remove_agents_md_link(self.target_dir, "CLAUDE.md")


class TestMain(unittest.TestCase):
    """Test the main entry point function."""

    def setUp(self):
        """Create temporary directories and save originals."""
        self.test_dir = tempfile.mkdtemp()
        self.commands_dir = Path(self.test_dir) / "commands"
        self.commands_dir.mkdir()
        self.home_dir = Path(self.test_dir) / "home"
        self.home_dir.mkdir()

        # Save original values
        self.original_home = sync_commands.HOME_DIR
        sync_commands.HOME_DIR = self.home_dir

        # Save original agents directory
        self.original_agents = Path("./agents").resolve()
        self.backup_agents = None
        if self.original_agents.exists():
            self.backup_agents = Path(self.test_dir) / "backup_agents"
            import shutil
            shutil.copytree(self.original_agents, self.backup_agents)

        # Create temporary agents directory for testing
        self.test_agents_dir = Path("./agents").resolve()
        if self.test_agents_dir.exists():
            import shutil
            shutil.rmtree(self.test_agents_dir)
        self.test_agents_dir.mkdir()

    def tearDown(self):
        """Clean up and restore originals."""
        import shutil
        sync_commands.HOME_DIR = self.original_home

        # Remove test agents directory
        if self.test_agents_dir.exists():
            shutil.rmtree(self.test_agents_dir)

        # Restore original agents if it was backed up
        if self.backup_agents and self.backup_agents.exists():
            shutil.copytree(self.backup_agents, self.original_agents)

        shutil.rmtree(self.test_dir)

    def test_exits_when_commands_dir_missing(self):
        """Function should return early when commands directory doesn't exist."""
        # Remove commands directory temporarily
        import shutil
        shutil.rmtree(self.commands_dir)

        # Run from the isolated temp project root and patch home to avoid touching real ~/
        import os
        original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        try:
            with unittest.mock.patch('pathlib.Path.home', return_value=self.home_dir):
                # Should return without error
                sync_commands.main()
        finally:
            os.chdir(original_cwd)

    def test_exits_when_no_toml_files(self):
        """Function should return early when no .toml files found."""
        # Empty commands directory; run from isolated temp project root and patch home
        import os
        original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        try:
            with unittest.mock.patch('pathlib.Path.home', return_value=self.home_dir):
                sync_commands.main()
        finally:
            os.chdir(original_cwd)

    def test_filters_claude_only_files(self):
        """Claude-only files should be filtered correctly."""
        # Create test files
        shared_file = self.commands_dir / "shared.toml"
        shared_file.write_text('prompt = "shared"\n')
        claude_file = self.commands_dir / "claude_test.toml"
        claude_file.write_text('prompt = "claude"\n')

        # Create .claude directory in home_dir (which is mocked HOME_DIR)
        claude_root = self.home_dir / ".claude"
        claude_root.mkdir(parents=True)

        # Change to test directory so main() finds the commands dir
        import os
        original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        try:
            # Mock Path.home() to return our home_dir
            with unittest.mock.patch('pathlib.Path.home', return_value=self.home_dir):
                sync_commands.main()

            # Check that files were processed for .claude
            # The claude_root is in test_dir/home/.claude
            self.assertTrue((claude_root / "commands").exists())
            # claude_test.toml -> test.md (prefix stripped)
            self.assertTrue((claude_root / "commands" / "test.md").exists())
            # shared.toml -> shared.md (no prefix to strip)
            self.assertTrue((claude_root / "commands" / "shared.md").exists())
        finally:
            os.chdir(original_cwd)

    def test_processes_shared_files(self):
        """Shared files should be processed for all tools."""
        shared_file = self.commands_dir / "shared.toml"
        shared_file.write_text('prompt = "shared"\n')

        # Create .claude directory
        claude_root = self.home_dir / ".claude"
        claude_root.mkdir(parents=True)

        # Change to test directory
        import os
        original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        try:
            # Mock Path.home() to return our home_dir
            with unittest.mock.patch('pathlib.Path.home', return_value=self.home_dir):
                sync_commands.main()

            # Files should be processed
            self.assertTrue((claude_root / "commands").exists())
            self.assertTrue((claude_root / "commands" / "shared.md").exists())
        finally:
            os.chdir(original_cwd)

    def test_skips_nonexistent_tool_dirs(self):
        """Non-existent tool directories should be skipped."""
        shared_file = self.commands_dir / "shared.toml"
        shared_file.write_text('prompt = "shared"\n')

        # Don't create any tool directories - they don't exist

        # Change to test directory
        import os
        original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        try:
            # Mock Path.home() to return our home_dir
            with unittest.mock.patch('pathlib.Path.home', return_value=self.home_dir):
                # Should not raise error
                sync_commands.main()
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
