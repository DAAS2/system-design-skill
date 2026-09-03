"""Unit tests for the minimal frontmatter parser in validate_skill.py.

Run: python -m unittest test_validate_skill -v
"""

import unittest

import validate_skill

parse = validate_skill.parse_minimal_frontmatter


class TestBasicParsing(unittest.TestCase):
    def test_simple_key_value(self):
        self.assertEqual(parse("name: my-skill"), {"name": "my-skill"})

    def test_multiple_keys(self):
        fm = parse("name: my-skill\ndescription: Does things\n")
        self.assertEqual(fm, {"name": "my-skill", "description": "Does things"})

    def test_no_space_after_colon(self):
        self.assertEqual(parse("name:foo"), {"name": "foo"})

    def test_value_whitespace_trimmed(self):
        self.assertEqual(parse("name:   foo   "), {"name": "foo"})

    def test_empty_value_becomes_empty_string(self):
        self.assertEqual(parse("name:"), {"name": ""})

    def test_value_may_contain_colons(self):
        self.assertEqual(parse("time: 12:30:45"), {"time": "12:30:45"})

    def test_hyphenated_key(self):
        self.assertEqual(parse("kebab-case-key: v"), {"kebab-case-key": "v"})

    def test_underscored_key(self):
        self.assertEqual(parse("snake_case: v"), {"snake_case": "v"})

    def test_duplicate_key_last_wins(self):
        self.assertEqual(parse("name: a\nname: b"), {"name": "b"})

    def test_empty_input(self):
        self.assertEqual(parse(""), {})

    def test_crlf_line_endings(self):
        self.assertEqual(
            parse("name: foo\r\ndescription: bar\r\n"),
            {"name": "foo", "description": "bar"},
        )


class TestKnownLimitations(unittest.TestCase):
    """Document current behavior that differs from real YAML."""

    def test_quotes_kept_verbatim(self):
        self.assertEqual(parse('name: "foo"'), {"name": '"foo"'})

    def test_trailing_hash_kept_verbatim(self):
        self.assertEqual(parse("name: foo # bar"), {"name": "foo # bar"})

    def test_digit_leading_key_is_accepted(self):
        self.assertEqual(parse("1key: v"), {"1key": "v"})

    def test_pipe_block_scalar_not_guarded(self):
        self.assertEqual(parse("description: |"), {"description": "|"})

    def test_continuation_lines_are_dropped(self):
        fm = parse("description: first line\n  second line\n")
        self.assertEqual(fm, {"description": "first line"})


class TestIgnoredLines(unittest.TestCase):
    def test_blank_lines_ignored(self):
        self.assertEqual(parse("\n\nname: foo\n\n"), {"name": "foo"})

    def test_line_without_colon_ignored(self):
        self.assertEqual(parse("just text\nname: foo"), {"name": "foo"})

    def test_comment_line_ignored(self):
        self.assertEqual(parse("# name: foo\nname: bar"), {"name": "bar"})

    def test_indented_line_ignored(self):
        self.assertEqual(parse("name: foo\n  nested: bar"), {"name": "foo"})

    def test_space_before_colon_ignored(self):
        self.assertEqual(parse("name : foo"), {})

    def test_key_must_not_start_with_hyphen(self):
        self.assertEqual(parse("-weird: foo"), {})


class TestFoldedScalarGuard(unittest.TestCase):
    def test_bare_folded_scalar_skipped(self):
        self.assertEqual(parse("description: >"), {})

    def test_chomped_folded_scalar_skipped(self):
        self.assertEqual(parse("description: >-"), {})

    def test_folded_scalar_with_inline_text_skipped(self):
        self.assertEqual(parse("description: > folded text"), {})


class TestRealisticFrontmatter(unittest.TestCase):
    def test_skill_frontmatter_shape(self):
        fm_text = (
            "name: system-design\n"
            "description: End-to-end system design for real codebases\n"
            "---\n"
        )
        fm = parse(fm_text)
        self.assertEqual(fm["name"], "system-design")
        self.assertTrue(fm["description"].startswith("End-to-end"))

    def test_long_description_stays_on_one_line(self):
        desc = "x" * 1000
        fm = parse(f"name: s\ndescription: {desc}\n")
        self.assertEqual(len(fm["description"]), 1000)


if __name__ == "__main__":
    unittest.main()
