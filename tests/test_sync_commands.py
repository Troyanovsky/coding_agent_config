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
        """Backslashes should be doubled."""
        result = sync_commands._escape_yaml_string(r"path\to\file")
        self.assertEqual(result, r"path\\to\\file")

    def test_combined_quotes_and_backslashes(self):
        """Both quotes and backslashes should be escaped."""
        result = sync_commands._escape_yaml_string(r"It's a \path")
        self.assertEqual(result, r"It''s a \\path")


class TestFormatYamlDescription(unittest.TestCase):
    """Test the _format_yaml_description function."""

    def test_simple_description(self):
        """Simple descriptions should format correctly."""
        result = sync_commands._format_yaml_description("A simple description")
        # With PyYAML: "description: A simple description" (no quotes)
        # Without PyYAML: "description: 'A simple description'"
        self.assertIn("description:", result)
        self.assertIn("A simple description", result)

    def test_special_yaml_characters(self):
        """Special YAML characters should be properly escaped."""
        description = "Use colons: and [brackets]"
        result = sync_commands._format_yaml_description(description)
        # Should be valid YAML - no unescaped special chars
        self.assertIn("description:", result)

    def test_colon_character(self):
        """Colons should not break YAML formatting."""
        description = "Step 1: Do something"
        result = sync_commands._format_yaml_description(description)
        self.assertIn("description:", result)

    def test_brackets(self):
        """Brackets should be properly handled."""
        description = "See [documentation](link)"
        result = sync_commands._format_yaml_description(description)
        self.assertIn("description:", result)

    def test_braces(self):
        """Braces should be properly handled."""
        description = "Use {key: value}"
        result = sync_commands._format_yaml_description(description)
        self.assertIn("description:", result)

    def test_unicode_characters(self):
        """Unicode characters should be preserved."""
        description = "Unicode: café, 日本語, emoji 🎉"
        result = sync_commands._format_yaml_description(description)
        self.assertIn("description:", result)
        # Unicode should be present, not escaped
        self.assertIn("café", result)

    def test_quotes_in_description(self):
        """Quotes should be properly escaped."""
        description = 'He said "hello"'
        result = sync_commands._format_yaml_description(description)
        self.assertIn("description:", result)

    def test_empty_string(self):
        """Empty strings should be handled."""
        result = sync_commands._format_yaml_description("")
        self.assertIn("description:", result)


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


if __name__ == "__main__":
    unittest.main()
