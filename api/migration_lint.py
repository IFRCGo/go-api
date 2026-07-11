"""Utilities for validating Django migration files."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

MIGRATION_FILENAME_RE = re.compile(r"^(?P<number>\d{4})_(?P<slug>.+)\.py$")
MERGE_SLUG_RE = re.compile(r"^merge_")


@dataclass
class MigrationLintIssue:
    level: str  # error | warning
    app: str
    path: str
    message: str


@dataclass
class MigrationLintResult:
    issues: list[MigrationLintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(issue.level == "error" for issue in self.issues)


def _ast_value(node: ast.AST):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Tuple):
        return tuple(_ast_value(elt) for elt in node.elts)
    if isinstance(node, ast.List):
        return [_ast_value(elt) for elt in node.elts]
    if isinstance(node, ast.Call):
        # migrations.swappable_dependency(...) — resolved by Django at runtime.
        return None
    raise ValueError(f"Unsupported AST node in migration file: {type(node).__name__}")


def _parse_dependencies(path: Path) -> list[tuple[str, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Migration":
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "dependencies":
                            return _ast_value(item.value)
    return []


def _discover_migration_apps(base_dir: Path) -> list[tuple[str, Path]]:
    apps: list[tuple[str, Path]] = []
    for migrations_dir in sorted(base_dir.glob("*/migrations")):
        if not migrations_dir.is_dir():
            continue
        app_label = migrations_dir.parent.name
        if app_label.startswith("."):
            continue
        apps.append((app_label, migrations_dir))
    return apps


def lint_migrations(base_dir: Path) -> MigrationLintResult:
    result = MigrationLintResult()
    known: dict[tuple[str, str], Path] = {}
    by_app_number: dict[tuple[str, str], list[str]] = {}
    parsed: dict[tuple[str, str], list[tuple[str, str]]] = {}

    for app_label, migrations_dir in _discover_migration_apps(base_dir):
        for path in sorted(migrations_dir.glob("*.py")):
            if path.name == "__init__.py":
                continue

            match = MIGRATION_FILENAME_RE.match(path.name)
            if not match:
                result.issues.append(
                    MigrationLintIssue(
                        level="error",
                        app=app_label,
                        path=str(path.relative_to(base_dir)),
                        message=(
                            "Invalid migration filename; expected NNNN_description.py "
                            f"(got {path.name})"
                        ),
                    )
                )
                continue

            number = match.group("number")
            slug = match.group("slug")
            migration_name = path.stem
            known[(app_label, migration_name)] = path
            by_app_number.setdefault((app_label, number), []).append(migration_name)

            try:
                raw_deps = _parse_dependencies(path)
                parsed[(app_label, migration_name)] = [
                    dep for dep in raw_deps if isinstance(dep, tuple) and len(dep) == 2
                ]
            except (SyntaxError, ValueError) as exc:
                result.issues.append(
                    MigrationLintIssue(
                        level="error",
                        app=app_label,
                        path=str(path.relative_to(base_dir)),
                        message=f"Could not parse dependencies: {exc}",
                    )
                )

            if slug.startswith("_"):
                result.issues.append(
                    MigrationLintIssue(
                        level="warning",
                        app=app_label,
                        path=str(path.relative_to(base_dir)),
                        message="Migration slug should not start with an underscore",
                    )
                )

    for (app_label, number), names in by_app_number.items():
        if len(names) <= 1:
            continue

        branch_names = [
            name
            for name in names
            if not MERGE_SLUG_RE.match(name.split("_", 1)[1] if "_" in name else "")
        ]
        if len(branch_names) <= 1:
            continue

        merged = False
        for (merge_app, merge_name), deps in parsed.items():
            if merge_app != app_label:
                continue
            slug = merge_name.split("_", 1)[1] if "_" in merge_name else merge_name
            if not MERGE_SLUG_RE.match(slug):
                continue
            dep_names = {dep_name for dep_app, dep_name in deps if dep_app == app_label}
            if set(branch_names).issubset(dep_names):
                merged = True
                break

        if not merged:
            result.issues.append(
                MigrationLintIssue(
                    level="warning",
                    app=app_label,
                    path=app_label,
                    message=(
                        f"Duplicate migration number {number} in app '{app_label}': "
                        f"{', '.join(sorted(branch_names))}. Add a merge migration if this is intentional."
                    ),
                )
            )

    app_labels = {app for app, _ in known}

    for (app_label, migration_name), dependencies in parsed.items():
        rel_path = known[(app_label, migration_name)].relative_to(base_dir)
        for dep_app, dep_name in dependencies:
            if dep_app not in app_labels:
                continue
            if (dep_app, dep_name) not in known:
                result.issues.append(
                    MigrationLintIssue(
                        level="error",
                        app=app_label,
                        path=str(rel_path),
                        message=f"Missing dependency target: ({dep_app!r}, {dep_name!r})",
                    )
                )

    return result
