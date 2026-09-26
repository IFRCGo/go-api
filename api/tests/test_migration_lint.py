import tempfile
import unittest
from pathlib import Path

from api.migration_lint import lint_migrations

REPO_ROOT = Path(__file__).resolve().parents[2]


class MigrationLintTests(unittest.TestCase):
    def test_existing_repo_migrations_have_valid_dependencies(self):
        result = lint_migrations(REPO_ROOT)
        errors = [issue for issue in result.issues if issue.level == "error"]
        self.assertEqual(errors, [])

    def test_flags_invalid_filename(self):
        with tempfile.TemporaryDirectory() as tempdir:
            base = Path(tempdir)
            migrations_dir = base / "sampleapp" / "migrations"
            migrations_dir.mkdir(parents=True)
            (migrations_dir / "__init__.py").write_text("")
            (migrations_dir / "bad-name.py").write_text(
                "from django.db import migrations\n\n"
                "class Migration(migrations.Migration):\n"
                "    dependencies = []\n"
                "    operations = []\n"
            )

            result = lint_migrations(base)
            self.assertFalse(result.ok)
            self.assertTrue(any("Invalid migration filename" in issue.message for issue in result.issues))

    def test_flags_missing_dependency(self):
        with tempfile.TemporaryDirectory() as tempdir:
            base = Path(tempdir)
            migrations_dir = base / "sampleapp" / "migrations"
            migrations_dir.mkdir(parents=True)
            (migrations_dir / "__init__.py").write_text("")
            (migrations_dir / "0001_initial.py").write_text(
                "from django.db import migrations\n\n"
                "class Migration(migrations.Migration):\n"
                "    dependencies = [('sampleapp', '9999_missing')]\n"
                "    operations = []\n"
            )

            result = lint_migrations(base)
            self.assertFalse(result.ok)
            self.assertTrue(any("Missing dependency target" in issue.message for issue in result.issues))


if __name__ == "__main__":
    unittest.main()
