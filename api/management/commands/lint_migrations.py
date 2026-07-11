from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from api.migration_lint import lint_migrations


class Command(BaseCommand):
    help = "Lint Django migration files for naming, duplicate numbers, and dependency issues."

    def add_arguments(self, parser):
        parser.add_argument(
            "--warnings-as-errors",
            action="store_true",
            help="Treat warnings as errors (useful in CI).",
        )

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)
        result = lint_migrations(base_dir)

        for issue in result.issues:
            line = f"[{issue.level.upper()}] {issue.app}/{issue.path}: {issue.message}"
            if issue.level == "error":
                self.stderr.write(line)
            else:
                self.stdout.write(line)

        if not result.issues:
            self.stdout.write(self.style.SUCCESS("No migration lint issues found."))
            return

        has_errors = not result.ok
        has_warnings = any(issue.level == "warning" for issue in result.issues)
        if has_errors or (options["warnings_as_errors"] and has_warnings):
            raise CommandError("Migration lint failed.")

        self.stdout.write(self.style.WARNING("Migration lint completed with warnings only."))
