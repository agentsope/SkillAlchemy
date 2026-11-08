import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_skill_metadata.py"
spec = importlib.util.spec_from_file_location("check_skill_metadata", SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class SkillMetadataTests(unittest.TestCase):
    def check_text(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "SKILL.md"
            path.write_text(text, encoding="utf-8")
            return checker.check_skill(path)

    def test_supported_text_forms_and_line_endings(self):
        for description in (
            "Useful skill",
            '"Useful skill" # note',
            "|-\n  Useful\n  skill",
            ">\n  Useful skill",
        ):
            for newline in ("\n", "\r\n"):
                with self.subTest(description=description, newline=newline):
                    text = f"---\nname: Lens\ndescription: {description}\n---\n# Body\n"
                    self.assertEqual(self.check_text(text.replace("\n", newline)), [])

    def test_empty_and_nontext_values_fail(self):
        for value in (
            "",
            '""',
            "'' # empty",
            "# comment",
            "[]",
            "{}",
            "null",
            "true",
            "123",
            "|\n  ",
        ):
            with self.subTest(value=value):
                self.assertTrue(
                    self.check_text(f"---\nname: test\ndescription: {value}\n---\n")
                )

    def test_body_and_nested_fields_cannot_supply_required_metadata(self):
        text = "---\nname: test\nextra:\n  description: nested\n---\ndescription: body example\n"
        self.assertTrue(self.check_text(text))

    def test_duplicate_required_field_fails(self):
        self.assertTrue(
            self.check_text("---\nname: one\nname: two\ndescription: Text\n---\n")
        )

    def test_missing_delimiters_fail(self):
        for text in (
            "name: test\ndescription: Text",
            "---\nname: test\ndescription: Text",
        ):
            with self.subTest(text=text):
                self.assertTrue(self.check_text(text))

    def test_cli_fails_for_package_without_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skills/missing").mkdir(parents=True)
            (root / "SKILL.md").write_text("---\nname: root\ndescription: Text\n---\n")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--root", str(root)],
                capture_output=True,
                text=True,
                cwd=directory,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("skills/missing/SKILL.md", result.stderr)

    def test_cli_defaults_to_repository_independently_of_cwd(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPT)],
                capture_output=True,
                text=True,
                cwd=directory,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OK: checked", result.stdout)


if __name__ == "__main__":
    unittest.main()
