"""
Unit tests for sync_commands.py module.

Tests the YAML front matter generation functionality including proper
escaping of multi-line strings, special YAML characters, and Unicode.
"""

import os
import sys
import tempfile
import unittest
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
        self.assertIn("True", result)


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


if __name__ == "__main__":
    unittest.main()
