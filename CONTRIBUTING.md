# Contributing to IFRC GO API

Thank you for helping improve the backend for [IFRC GO](https://go.ifrc.org/). This document covers local setup, code style, tests, and pull requests.

For day-to-day commands (migrations, shell, server, translations), see [README.md](./README.md). For test patterns and snapshots, see [TESTING.md](./TESTING.md).

## Getting started

### Docker (recommended)

Requirements: Docker and Docker Compose.

```bash
docker-compose build
docker-compose run --rm migrate
docker-compose run --rm loaddata
docker-compose up serve celery
```

API: http://localhost:8000

Run the test suite:

```bash
docker-compose run --rm test
```

### uv (optional local Python)

Python **3.11** (see `.python-version` and `pyproject.toml`). Copy `.env-sample` and set required variables from `main/settings.py` (at minimum `DJANGO_SECRET_KEY`, `API_FQDN`, `FRONTEND_URL`).

```bash
uv sync
uv run python manage.py --help
```

Most contributors still run tests through Docker because of PostGIS, GDAL, and service dependencies.

## Pull requests

- Branch from **`develop`** (default integration branch).
- **One issue → one branch → one PR.** Link the issue in the PR description (see [.github/pull_request_template.md](./.github/pull_request_template.md)).
- Comment on the linked issue with the PR URL and a short test summary when you open the PR.
- Keep PRs focused; avoid unrelated refactors.
- CI must pass: pre-commit, migrations check, OpenAPI schema check, and pytest (see [.github/workflows/ci.yml](./.github/workflows/ci.yml)).

## Code style

Formatting and lint config lives in:

| Tool | Config |
|------|--------|
| [Black](https://black.readthedocs.io/) | `pyproject.toml` (`line-length = 130`) |
| [isort](https://pycqa.github.io/isort/) | `pyproject.toml` (profile `black`) |
| [flake8](https://flake8.pycqa.org/) | `.flake8` (`max-line-length = 130`, migrations/snapshots excluded) |

Migrations and snapshot files are excluded from formatters; do not hand-edit generated snapshot files.

### Pre-commit

Install hooks once:

```bash
uv sync
uv run pre-commit install
```

Run on all files:

```bash
uv run pre-commit run --all-files
```

CI runs the same hooks in the **Pre-Commit checks** job.

## Tests

- **Preferred:** `docker-compose run --rm test` (pytest).
- **Snapshot tests:** see [TESTING.md](./TESTING.md). Update snapshots with `docker-compose run --rm test_snapshot_update` only when the API change is intentional.
- **Coverage:** `docker-compose run --rm coverage_report` or `coverage_html`.

When adding tests:

- Create explicit fixtures (factories or `setUp` data). Do not rely on migration-seeded lookup rows unless the test creates them.
- Use `factory_boy` factories where they already exist under `<app>/factories/`.
- For DRF/API tests, follow patterns in existing `test_views.py` / `tests.py` files and `main/test_case.py`.

## Database migrations

Create migrations inside Docker:

```bash
docker-compose run --rm makemigrations
docker-compose run --rm migrate
```

If two branches add migrations with conflicting numbers, merge them:

```bash
docker-compose run --rm makemigrations_merge
```

CI fails if `makemigrations --check --dry-run` detects model changes without a migration.

## API schema

If you change serializers or views that affect the OpenAPI schema, regenerate and commit `assets/openapi-schema.yaml`:

```bash
docker compose run --rm serve ./manage.py spectacular --file openapi-schema-latest.yaml
# diff against assets/openapi-schema.yaml and update if needed
```

CI compares the committed schema to a freshly generated one.

## Questions

- Open a [GitHub issue](https://github.com/IFRCGo/go-api/issues) for bugs or feature requests.
- Use the issue templates under `.github/ISSUE_TEMPLATE/` for production/staging bugs and feature requests.
