from django.core.management.base import BaseCommand
from django.db import connection

from dref.models import (  # PlannedInterventionIndicators,
    Dref,
    DrefOperationalUpdate,
    PlannedIntervention,
)

try:  # pragma: no cover - optional model
    from dref.models import DrefFinalReport  # noqa: F401
except Exception:  # pragma: no cover
    DrefFinalReport = None  # type: ignore


def _through_table_and_column_names():
    """Return list of (table_name, planned_intervention_fk_column) for M2M relations.

    We inspect the through model fields to locate the column referencing PlannedIntervention
    instead of assuming naming conventions. This makes the command resilient and allows
    us to build efficient NOT EXISTS predicates (better than large UNIONs).
    """
    out = []
    for model in (Dref, DrefOperationalUpdate):
        through = model.planned_interventions.through
        tbl = through._meta.db_table
        fk_col = None
        for f in through._meta.get_fields():
            if getattr(f, "related_model", None) == PlannedIntervention and hasattr(f, "column"):
                fk_col = f.column
                break
        if fk_col:
            out.append((tbl, fk_col))
    if DrefFinalReport is not None and hasattr(DrefFinalReport, "planned_interventions"):
        through = DrefFinalReport.planned_interventions.through
        tbl = through._meta.db_table
        fk_col = None
        for f in through._meta.get_fields():
            if getattr(f, "related_model", None) == PlannedIntervention and hasattr(f, "column"):
                fk_col = f.column
                break
        if fk_col:
            out.append((tbl, fk_col))
    return out


def _indicator_through_table_and_fk():
    """Return (through_table, fk_column) for PlannedIntervention.indicators M2M if present."""
    if not hasattr(PlannedIntervention, "indicators"):
        return None, None
    through = PlannedIntervention.indicators.through
    table = through._meta.db_table
    fk_col = None
    for f in through._meta.get_fields():
        if getattr(f, "related_model", None) == PlannedIntervention and hasattr(f, "column"):
            fk_col = f.column
            break
    return (table, fk_col) if fk_col else (None, None)


def build_raw_sql():
    """Return optimized SQL selecting dangling planned interventions using NOT EXISTS.

    This avoids building large UNION sets and DISTINCT scans, leveraging indexes on
    through tables for faster anti-joins.
    """
    link_tables = _through_table_and_column_names()
    indicator_table, indicator_fk = _indicator_through_table_and_fk()
    predicates = []
    for tbl, fk_col in link_tables:
        predicates.append(f"NOT EXISTS (SELECT 1 FROM {tbl} rel WHERE rel.{fk_col} = pi.id)")
    if indicator_table and indicator_fk:
        predicates.append(f"NOT EXISTS (SELECT 1 FROM {indicator_table} rel WHERE rel.{indicator_fk} = pi.id)")
    where_clause = " AND\n        ".join(predicates) if predicates else "TRUE"  # if no relations defined
    return f"""
SELECT pi.id
FROM dref_plannedintervention pi
WHERE {where_clause}
ORDER BY pi.id;
"""


def build_stats_sql():
    """Return optimized stats SQL using NOT EXISTS for dangling and arithmetic for referenced unique.

    Eliminates DISTINCT across UNION; computes dangling via same predicates used in raw listing.
    """
    link_tables = _through_table_and_column_names()
    indicator_table, indicator_fk = _indicator_through_table_and_fk()
    predicates = []
    for tbl, fk_col in link_tables:
        predicates.append(f"NOT EXISTS (SELECT 1 FROM {tbl} rel WHERE rel.{fk_col} = pi.id)")
    if indicator_table and indicator_fk:
        predicates.append(f"NOT EXISTS (SELECT 1 FROM {indicator_table} rel WHERE rel.{indicator_fk} = pi.id)")
    where_clause = " AND\n        ".join(predicates) if predicates else "TRUE"

    # Build individual CTEs for link counts
    ctes = []
    for i, (tbl, _) in enumerate(link_tables):
        ctes.append(f"t{i} AS (SELECT COUNT(*) AS c FROM {tbl})")
    final_report_idx = 2 if len(link_tables) >= 3 else None
    if indicator_table:
        ctes.append(f"ti AS (SELECT COUNT(*) AS c FROM {indicator_table})")
    ctes.append("total_interventions AS (SELECT COUNT(*) AS c FROM dref_plannedintervention)")
    ctes.append(f"dangling AS (SELECT pi.id FROM dref_plannedintervention pi WHERE {where_clause})")
    ctes_sql = ",\n    ".join(ctes)
    final_report_select = (
        "NULL AS dref_final_report_links,"
        if final_report_idx is None
        else f"(SELECT c FROM t{final_report_idx}) AS dref_final_report_links,"
    )
    indicators_select = "NULL AS indicators_links," if not indicator_table else "(SELECT c FROM ti) AS indicators_links,"
    return f"""
WITH
    {ctes_sql}
SELECT
    (SELECT c FROM total_interventions) AS total_interventions,
    ((SELECT c FROM total_interventions) - (SELECT COUNT(*) FROM dangling)) AS total_referenced_unique,
    (SELECT c FROM t0) AS dref_links,
    {("(SELECT c FROM t1)" if len(link_tables) > 1 else "NULL")} AS dref_operational_update_links,
    {final_report_select}
    {indicators_select}
    (SELECT COUNT(*) FROM dangling) AS dangling_estimate
;"""


class Command(BaseCommand):
    help = "List PlannedIntervention rows not linked to any Dref / DrefOperationalUpdate / DrefFinalReport (dangling)."

    def add_arguments(self, parser):
        parser.add_argument("--sql", action="store_true", help="Print the raw SQL that will be executed.")
        parser.add_argument("--count", action="store_true", help="Print only the count of dangling rows.")
        parser.add_argument("--verbose", action="store_true", help="List dangling IDs (and titles) before stats.")
        parser.add_argument(
            "--move-danglings",
            action="store_true",
            help="Move dangling records to tmp_dref_plannedintervention and delete them from original table.",
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
            self.stdout.write(f"Dangling PlannedIntervention count: {len(rows)}")
            return

        if not rows:
            self.stdout.write("No dangling PlannedIntervention records found.")
            with connection.cursor() as cursor:
                cursor.execute(stats_sql)
                stats_row = cursor.fetchone()
            self._print_stats(stats_row)
            return

        if options.get("verbose"):
            self.stdout.write(f"Found {len(rows)} dangling PlannedIntervention record(s):")
            for pk in rows:
                self.stdout.write(f" - {pk}")
            interventions = PlannedIntervention.objects.filter(pk__in=rows).only("pk", "title")
            for intervention in interventions:
                self.stdout.write(f"   > {intervention.pk}: {intervention.title}")

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
        self.stdout.write("\n-- Moving dangling rows to tmp_dref_plannedintervention --")
        id_list_sql = ",".join(str(i) for i in dangling_ids)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tmp_dref_plannedintervention (LIKE dref_plannedintervention INCLUDING ALL);
                TRUNCATE TABLE tmp_dref_plannedintervention;
                INSERT INTO tmp_dref_plannedintervention SELECT * FROM dref_plannedintervention WHERE id IN ("""
                + id_list_sql
                + ");"
            )
            cursor.execute("DELETE FROM dref_plannedintervention WHERE id IN (" + id_list_sql + ")")
        self.stdout.write(f"Moved {len(dangling_ids)} rows to tmp_dref_plannedintervention and deleted originals.")

    def _print_stats(self, stats_row, dangling_count=None):
        (
            total_interventions,
            total_referenced_unique,
            dref_links,
            op_update_links,
            final_report_links,
            indicators_links,
            dangling_estimate,
        ) = stats_row
        if dangling_count is None:
            dangling_count = dangling_estimate
        used_pct = (total_referenced_unique / total_interventions * 100.0) if total_interventions else 0.0
        dangling_pct = (dangling_count / total_interventions * 100.0) if total_interventions else 0.0
        self.stdout.write("\n=== PlannedIntervention Usage Stats ===")
        self.stdout.write(f"Total interventions: {total_interventions}")
        self.stdout.write(f"Referenced (unique across all DREF*): {total_referenced_unique} ({used_pct:.2f}%)")
        self.stdout.write(f"Dangling: {dangling_count} ({dangling_pct:.2f}%)")
        self.stdout.write("Breakdown (raw link table row counts):")
        self.stdout.write(f"  Dref links: {dref_links}")
        self.stdout.write(f"  OperationalUpdate links: {op_update_links}")
        self.stdout.write(f"  FinalReport links: {final_report_links if final_report_links is not None else 'N/A'}")
        self.stdout.write(f"  Indicators links: {indicators_links}")
