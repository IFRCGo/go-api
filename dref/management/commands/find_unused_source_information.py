from django.core.management.base import BaseCommand
from django.db import connection

from dref.models import Dref, DrefOperationalUpdate

try:  # pragma: no cover
    from dref.models import DrefFinalReport  # noqa: F401
except Exception:  # pragma: no cover
    DrefFinalReport = None  # type: ignore


def _through_table_and_column_names():
    """Return (table_names, fk_column_name) for the M2M 'source_information' relations."""
    tables = []
    fk_col = "sourceinformation_id"
    for model in (Dref, DrefOperationalUpdate):
        tables.append(model.source_information.through._meta.db_table)
    if DrefFinalReport is not None and hasattr(DrefFinalReport, "source_information"):
        tables.append(DrefFinalReport.source_information.through._meta.db_table)
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
FROM dref_sourceinformation
WHERE id NOT IN (SELECT id FROM referenced)
ORDER BY id;
"""


def build_stats_sql():
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
    total_items AS (SELECT COUNT(*) AS c FROM dref_sourceinformation)
SELECT
    (SELECT c FROM total_items) AS total_source_information,
    (SELECT c FROM total_refs) AS total_referenced_unique,
    (SELECT c FROM t0) AS dref_links,
    (SELECT c FROM t1) AS dref_operational_update_links,
    {'NULL AS dref_final_report_links,' if len(tables) < 3 else '(SELECT c FROM t2) AS dref_final_report_links,'}
    (SELECT c FROM total_items) - (SELECT c FROM total_refs) AS dangling_estimate
;"""


class Command(BaseCommand):
    help = "List SourceInformation rows not linked via any 'source_information' M2M field (dangling)."

    def add_arguments(self, parser):
        parser.add_argument("--sql", action="store_true", help="Print the raw SQL that will be executed.")
        parser.add_argument("--count", action="store_true", help="Print only the count of dangling rows.")
        parser.add_argument("--verbose", action="store_true", help="List dangling IDs before stats.")
        parser.add_argument(
            "--move-danglings",
            action="store_true",
            help="Archive dangling rows to tmp_dref_sourceinformation then delete originals.",
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
            self.stdout.write(f"Dangling SourceInformation count: {len(rows)}")
            return

        if not rows:
            self.stdout.write("No dangling SourceInformation records found.")
            with connection.cursor() as cursor:
                cursor.execute(stats_sql)
                stats_row = cursor.fetchone()
            self._print_stats(stats_row)
            return

        if options.get("verbose"):
            self.stdout.write(f"Found {len(rows)} dangling SourceInformation record(s):")
            for pk in rows:
                self.stdout.write(f" - {pk}")

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
        self.stdout.write("\n-- Moving dangling rows to tmp_dref_sourceinformation --")
        id_list_sql = ",".join(str(i) for i in dangling_ids)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tmp_dref_sourceinformation (LIKE dref_sourceinformation INCLUDING ALL);
                TRUNCATE TABLE tmp_dref_sourceinformation;
                INSERT INTO tmp_dref_sourceinformation SELECT * FROM dref_sourceinformation WHERE id IN ("""
                + id_list_sql
                + ");"
            )
            cursor.execute("DELETE FROM dref_sourceinformation WHERE id IN (" + id_list_sql + ")")
        self.stdout.write(f"Moved {len(dangling_ids)} rows to tmp_dref_sourceinformation and deleted originals.")

    def _print_stats(self, stats_row, dangling_count=None):
        (
            total_items,
            total_referenced_unique,
            dref_links,
            op_update_links,
            final_report_links,
            dangling_estimate,
        ) = stats_row
        if dangling_count is None:
            dangling_count = dangling_estimate
        used_pct = (total_referenced_unique / total_items * 100.0) if total_items else 0.0
        dangling_pct = (dangling_count / total_items * 100.0) if total_items else 0.0
        self.stdout.write("\n=== SourceInformation Usage Stats ===")
        self.stdout.write(f"Total source_information items: {total_items}")
        self.stdout.write(f"Referenced (unique across all DREF*): {total_referenced_unique} ({used_pct:.2f}%)")
        self.stdout.write(f"Dangling: {dangling_count} ({dangling_pct:.2f}%)")
        self.stdout.write("Breakdown (raw link table row counts):")
        self.stdout.write(f"  Dref links: {dref_links}")
        self.stdout.write(f"  OperationalUpdate links: {op_update_links}")
        self.stdout.write(f"  FinalReport links: {final_report_links if final_report_links is not None else 'N/A'}")
