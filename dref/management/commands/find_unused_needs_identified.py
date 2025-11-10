from django.core.management.base import BaseCommand
from django.db import connection

from dref.models import Dref, DrefOperationalUpdate, IdentifiedNeed

try:  # pragma: no cover - optional model presence
    from dref.models import DrefFinalReport  # noqa: F401
except Exception:  # pragma: no cover
    DrefFinalReport = None  # type: ignore


def _through_table_and_column_names():
    """Return (table_names, fk_column_name) for the three M2M 'needs_identified' relations.

    Django auto-generates the implicit through model with columns: <left>_id, <right>_id.
    For IdentifiedNeed the related FK column becomes 'identifiedneed_id'. We derive table
    names dynamically so the command stays resilient to future rename/migration changes.
    """
    tables = []
    fk_col = "identifiedneed_id"

    for model in (Dref, DrefOperationalUpdate):
        tables.append(model.needs_identified.through._meta.db_table)
    if DrefFinalReport is not None and hasattr(DrefFinalReport, "needs_identified"):
        tables.append(DrefFinalReport.needs_identified.through._meta.db_table)
    return tables, fk_col


def build_raw_sql():
    tables, fk = _through_table_and_column_names()
    union_parts = [f"SELECT {fk} AS id FROM {t}" for t in tables]
    union_sql = "\n    UNION\n    ".join(union_parts)
    return f"""
WITH referenced AS (
    {union_sql}
)
SELECT id
FROM dref_identifiedneed
WHERE id NOT IN (SELECT id FROM referenced)
ORDER BY id;
"""


def build_stats_sql():
    """Return SQL computing per-table usage counts and a dangling estimate for IdentifiedNeed."""
    tables, fk = _through_table_and_column_names()
    per_table_ctes = []
    for i, t in enumerate(tables):
        per_table_ctes.append(f"t{i} AS (SELECT COUNT(*) AS c FROM {t})")
    union_parts = [f"SELECT {fk} AS id FROM {t}" for t in tables]
    union_sql = " UNION ".join(union_parts)
    ctes_sql = ",\n    ".join(per_table_ctes)
    return f"""
WITH
    {ctes_sql},
    all_refs AS ({union_sql}),
    total_refs AS (SELECT COUNT(DISTINCT id) AS c FROM all_refs),
    total_needs AS (SELECT COUNT(*) AS c FROM dref_identifiedneed)
SELECT
    (SELECT c FROM total_needs) AS total_needs,
    (SELECT c FROM total_refs) AS total_referenced_unique,
    (SELECT c FROM t0) AS dref_links,
    (SELECT c FROM t1) AS dref_operational_update_links,
    {'NULL AS dref_final_report_links,' if len(tables) < 3 else '(SELECT c FROM t2) AS dref_final_report_links,'}
    (SELECT c FROM total_needs) - (SELECT c FROM total_refs) AS dangling_estimate
;"""


class Command(BaseCommand):
    help = "List IdentifiedNeed rows not linked to any Dref / DrefOperationalUpdate / DrefFinalReport (dangling)."

    def add_arguments(self, parser):
        parser.add_argument("--sql", action="store_true", help="Print the raw SQL that will be executed.")
        parser.add_argument("--count", action="store_true", help="Print only the count of dangling rows.")
        parser.add_argument("--verbose", action="store_true", help="List dangling IDs (and titles) before stats.")
        parser.add_argument(
            "--move-danglings",
            action="store_true",
            help="Move dangling records to tmp_dref_identifiedneed and delete them from original table.",
        )

    def handle(self, *args, **options):
        raw_sql = build_raw_sql()
        stats_sql = build_stats_sql()
        if options.get("sql"):
            self.stdout.write(raw_sql)
            self.stdout.write("\n-- Stats SQL --\n" + stats_sql)

        with connection.cursor() as cursor:
            cursor.execute(raw_sql)
            rows = [r[0] for r in cursor.fetchall()]

        if options.get("count"):
            self.stdout.write(f"Dangling IdentifiedNeed count: {len(rows)}")
            return

        if not rows:
            self.stdout.write("No dangling IdentifiedNeed records found.")
            with connection.cursor() as cursor:
                cursor.execute(stats_sql)
                stats_row = cursor.fetchone()
            self._print_stats(stats_row)
            return

        if options.get("verbose"):
            self.stdout.write(f"Found {len(rows)} dangling IdentifiedNeed record(s):")
            for pk in rows:
                self.stdout.write(f" - {pk}")
            needs = IdentifiedNeed.objects.filter(pk__in=rows).only("pk", "title")
            for need in needs:
                self.stdout.write(f"   > {need.pk}: {need.title}")

        with connection.cursor() as cursor:
            cursor.execute(stats_sql)
            stats_row = cursor.fetchone()
        self._print_stats(stats_row, len(rows))

        if options.get("move_danglings"):
            self._move_danglings(rows)

    def _move_danglings(self, dangling_ids):
        if not dangling_ids:
            self.stdout.write("No dangling rows to move.")
            return
        self.stdout.write("\n-- Moving dangling rows to tmp_dref_identifiedneed --")
        id_list_sql = ",".join(str(i) for i in dangling_ids)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tmp_dref_identifiedneed (LIKE dref_identifiedneed INCLUDING ALL);
                TRUNCATE TABLE tmp_dref_identifiedneed;
                INSERT INTO tmp_dref_identifiedneed SELECT * FROM dref_identifiedneed WHERE id IN ("""
                + id_list_sql
                + ");"
            )
            cursor.execute("DELETE FROM dref_identifiedneed WHERE id IN (" + id_list_sql + ")")
        self.stdout.write(f"Moved {len(dangling_ids)} rows to tmp_dref_identifiedneed and deleted originals.")

    def _print_stats(self, stats_row, dangling_count=None):
        (
            total_needs,
            total_referenced_unique,
            dref_links,
            op_update_links,
            final_report_links,
            dangling_estimate,
        ) = stats_row
        if dangling_count is None:
            dangling_count = dangling_estimate
        used_pct = (total_referenced_unique / total_needs * 100.0) if total_needs else 0.0
        dangling_pct = (dangling_count / total_needs * 100.0) if total_needs else 0.0
        self.stdout.write("\n=== IdentifiedNeed Usage Stats ===")
        self.stdout.write(f"Total identified needs: {total_needs}")
        self.stdout.write(f"Referenced (unique across all DREF*): {total_referenced_unique} ({used_pct:.2f}%)")
        self.stdout.write(f"Dangling: {dangling_count} ({dangling_pct:.2f}%)")
        self.stdout.write("Breakdown (raw link table row counts):")
        self.stdout.write(f"  Dref links: {dref_links}")
        self.stdout.write(f"  OperationalUpdate links: {op_update_links}")
        self.stdout.write(f"  FinalReport links: {final_report_links if final_report_links is not None else 'N/A'}")
