from django.core.management.base import BaseCommand
from django.db import connection

from dref.models import PlannedIntervention, PlannedInterventionIndicators


def _through_table_and_column_name():
    """Return (table_name, indicator_fk_column) for PlannedIntervention.indicators M2M."""
    if not hasattr(PlannedIntervention, "indicators"):
        return None, None
    through = PlannedIntervention.indicators.through
    table = through._meta.db_table
    fk_col = None
    for f in through._meta.get_fields():
        if getattr(f, "related_model", None) == PlannedInterventionIndicators and hasattr(f, "column"):
            fk_col = f.column
            break
    return (table, fk_col) if fk_col else (None, None)


def build_raw_sql():
    """Select indicator IDs not referenced by any PlannedIntervention via M2M."""
    through_table, indicator_fk = _through_table_and_column_name()
    if not through_table or not indicator_fk:
        # No M2M defined; treat all as dangling
        return "SELECT id FROM dref_plannedinterventionindicators ORDER BY id;"
    return f"""
SELECT pi.id
FROM dref_plannedinterventionindicators pi
WHERE NOT EXISTS (
    SELECT 1 FROM {through_table} rel WHERE rel.{indicator_fk} = pi.id
)
ORDER BY pi.id;
"""


def build_stats_sql():
    """Stats: total, referenced, dangling counts."""
    through_table, indicator_fk = _through_table_and_column_name()
    ctes = [
        "total_indicators AS (SELECT COUNT(*) AS c FROM dref_plannedinterventionindicators)",
        (
            f"dangling AS (SELECT pi.id FROM dref_plannedinterventionindicators pi WHERE NOT EXISTS "
            f"(SELECT 1 FROM {through_table} rel WHERE rel.{indicator_fk} = pi.id))"
            if through_table and indicator_fk
            else "dangling AS (SELECT id FROM dref_plannedinterventionindicators)"
        ),
        (
            f"refs AS (SELECT COUNT(DISTINCT {indicator_fk}) AS c FROM {through_table})"
            if through_table and indicator_fk
            else "refs AS (SELECT 0 AS c)"
        ),
    ]
    ctes_sql = ",\n    ".join(ctes)
    return f"""
WITH
    {ctes_sql}
SELECT
    (SELECT c FROM total_indicators) AS total_indicators,
    (SELECT c FROM refs) AS total_referenced_unique,
    (SELECT COUNT(*) FROM dangling) AS dangling_estimate
;"""


class Command(BaseCommand):
    help = "List PlannedInterventionIndicators rows not linked to any PlannedIntervention (dangling)."

    def add_arguments(self, parser):
        parser.add_argument("--sql", action="store_true", help="Print the raw SQL that will be executed.")
        parser.add_argument("--count", action="store_true", help="Print only the count of dangling rows.")
        parser.add_argument("--verbose", action="store_true", help="List dangling IDs before stats.")
        parser.add_argument(
            "--move-danglings",
            action="store_true",
            help="Move dangling records to tmp_dref_plannedinterventionindicators and delete them from original table.",
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
            self.stdout.write(f"Dangling PlannedInterventionIndicators count: {len(rows)}")
            return

        if not rows:
            self.stdout.write("No dangling PlannedInterventionIndicators records found.")
            with connection.cursor() as cursor:
                cursor.execute(stats_sql)
                stats_row = cursor.fetchone()
            self._print_stats(stats_row)
            return

        if options.get("verbose"):
            self.stdout.write(f"Found {len(rows)} dangling PlannedInterventionIndicators record(s):")
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
        self.stdout.write("\n-- Moving dangling rows to tmp_dref_plannedinterventionindicators --")
        id_list_sql = ",".join(str(i) for i in dangling_ids)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tmp_dref_plannedinterventionindicators
                (LIKE dref_plannedinterventionindicators INCLUDING ALL);
                TRUNCATE TABLE tmp_dref_plannedinterventionindicators;
                INSERT INTO tmp_dref_plannedinterventionindicators
                SELECT * FROM dref_plannedinterventionindicators WHERE id IN ("""
                + id_list_sql
                + ");"
            )
            cursor.execute("DELETE FROM dref_plannedinterventionindicators WHERE id IN (" + id_list_sql + ")")
        self.stdout.write(f"Moved {len(dangling_ids)} rows to tmp_dref_plannedinterventionindicators and deleted originals.")

    def _print_stats(self, stats_row, dangling_count=None):
        (
            total_indicators,
            total_referenced_unique,
            dangling_estimate,
        ) = stats_row
        if dangling_count is None:
            dangling_count = dangling_estimate
        used_pct = (total_referenced_unique / total_indicators * 100.0) if total_indicators else 0.0
        dangling_pct = (dangling_count / total_indicators * 100.0) if total_indicators else 0.0
        self.stdout.write("\n=== PlannedInterventionIndicators Usage Stats ===")
        self.stdout.write(f"Total indicators: {total_indicators}")
        self.stdout.write(f"Referenced (unique across all PlannedIntervention): {total_referenced_unique} ({used_pct:.2f}%)")
        self.stdout.write(f"Dangling: {dangling_count} ({dangling_pct:.2f}%)")
