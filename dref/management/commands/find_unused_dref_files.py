from django.core.management.base import BaseCommand
from django.db import connection, models

from dref.models import Dref, DrefFile, DrefOperationalUpdate

try:  # pragma: no cover
    from dref.models import DrefFinalReport  # noqa: F401
except Exception:  # pragma: no cover
    DrefFinalReport = None  # type: ignore


def _all_file_m2m_through_tables():
    """Return list of (table_name, fk_column, rel_type) for BOTH images and photos M2M relations."""
    tables = []
    seen = set()
    for model in (Dref, DrefOperationalUpdate, DrefFinalReport if DrefFinalReport else None):
        if not model:
            continue
        for attr in ("images", "photos"):
            if hasattr(model, attr):
                rel = getattr(model, attr)
                through = rel.through
                tbl = through._meta.db_table
                if tbl in seen:
                    continue
                fk_col = None
                for f in through._meta.get_fields():
                    if getattr(f, "related_model", None) == DrefFile and hasattr(f, "column"):
                        fk_col = f.column
                        break
                if fk_col:
                    tables.append((tbl, fk_col, attr))
                    seen.add(tbl)
    return tables


def _direct_fk_tables():
    """Return list of (table_name, fk_column) for forward ForeignKey fields in DREF models pointing to DrefFile.

    Reverse relations (ForeignObjectRel) and M2M are excluded; we only want concrete columns physically on the model's table.
    Covers columns like event_map_id (and any future direct FK) ensuring they count as usage.
    """
    out = []
    for model in (Dref, DrefOperationalUpdate, DrefFinalReport if DrefFinalReport else None):
        if not model:
            continue
        tbl = model._meta.db_table
        for f in model._meta.get_fields():
            if isinstance(f, models.ForeignKey) and f.remote_field and f.remote_field.model == DrefFile and f.concrete:
                out.append((tbl, f.column))
    return out


def build_raw_sql():
    """SQL selecting file IDs not referenced in ANY images/photos M2M OR direct FK columns."""
    link_tables = _all_file_m2m_through_tables()
    direct_fks = _direct_fk_tables()
    if not link_tables and not direct_fks:
        return "SELECT id FROM dref_dreffile ORDER BY id;"  # everything considered dangling
    predicates = []
    for tbl, fk, _rel in link_tables:
        predicates.append(f"NOT EXISTS (SELECT 1 FROM {tbl} rel WHERE rel.{fk} = f.id)")
    for tbl, fk in direct_fks:
        predicates.append(f"NOT EXISTS (SELECT 1 FROM {tbl} rel WHERE rel.{fk} = f.id)")
    where_clause = " AND\n        ".join(predicates)
    return f"""
SELECT f.id
FROM dref_dreffile f
WHERE {where_clause}
ORDER BY f.id;
"""


def build_stats_sql():
    """Stats including images/photos M2M link rows, direct FK references, and dangling counts."""
    link_tables = _all_file_m2m_through_tables()
    direct_fks = _direct_fk_tables()

    ctes = ["total_files AS (SELECT COUNT(*) AS c FROM dref_dreffile)"]
    per_table_labels = []
    for idx, (tbl, fk, rel_name) in enumerate(link_tables):
        label = f"m{idx}"
        ctes.append(f"{label} AS (SELECT COUNT(*) AS c FROM {tbl})")
        per_table_labels.append((label, rel_name))
    for idx, (tbl, fk) in enumerate(direct_fks):
        label = f"d{idx}"
        ctes.append(f"{label} AS (SELECT COUNT(*) AS c FROM {tbl} WHERE {fk} IS NOT NULL)")

    # Dangling predicate uses both sets of references
    predicates = []
    for tbl, fk, _rel in link_tables:
        predicates.append(f"NOT EXISTS (SELECT 1 FROM {tbl} rel WHERE rel.{fk} = f.id)")
    for tbl, fk in direct_fks:
        predicates.append(f"NOT EXISTS (SELECT 1 FROM {tbl} rel WHERE rel.{fk} = f.id)")
    if predicates:
        where_clause = " AND\n        ".join(predicates)
        ctes.append(f"dangling AS (SELECT f.id FROM dref_dreffile f WHERE {where_clause})")
    else:
        ctes.append("dangling AS (SELECT id FROM dref_dreffile)")

    ctes_sql = ",\n    ".join(ctes)

    images_sum = []
    photos_sum = []
    for label, rel_name in per_table_labels:
        if rel_name == "images":
            images_sum.append(f"(SELECT c FROM {label})")
        elif rel_name == "photos":
            photos_sum.append(f"(SELECT c FROM {label})")
    images_expr = " + ".join(images_sum) if images_sum else "0"
    photos_expr = " + ".join(photos_sum) if photos_sum else "0"

    direct_fk_expr_parts = [f"(SELECT c FROM d{idx})" for idx, _ in enumerate(direct_fks)]
    direct_fk_expr = " + ".join(direct_fk_expr_parts) if direct_fk_expr_parts else "0"

    return f"""
WITH
    {ctes_sql}
SELECT
    (SELECT c FROM total_files) AS total_files,
    ((SELECT c FROM total_files) - (SELECT COUNT(*) FROM dangling)) AS total_referenced_unique,
    {images_expr} AS images_link_rows,
    {photos_expr} AS photos_link_rows,
    {direct_fk_expr} AS direct_fk_rows,
    (SELECT COUNT(*) FROM dangling) AS dangling_estimate
;"""


class Command(BaseCommand):
    help = (
        "List DrefFile rows not referenced via any images/photos M2M relations or direct FK columns (dangling). "
        "Combines previous separate checks to avoid partial deletions and accounts for direct foreign key usage (e.g. event_map)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--sql", action="store_true", help="Print the raw SQL that will be executed.")
        parser.add_argument("--count", action="store_true", help="Print only the count of dangling rows.")
        parser.add_argument("--verbose", action="store_true", help="List dangling IDs before stats.")
        parser.add_argument(
            "--move-danglings",
            action="store_true",
            help="Archive dangling rows to tmp_dref_dreffile_combined then delete originals.",
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
            self.stdout.write(f"Dangling DrefFile (images+photos+direct_fk) count: {len(rows)}")
            return

        if not rows:
            self.stdout.write("No dangling DrefFile records (images+photos+direct_fk) found.")
            with connection.cursor() as cursor:
                cursor.execute(stats_sql)
                stats_row = cursor.fetchone()
            self._print_stats(stats_row)
            return

        if options.get("verbose"):
            self.stdout.write(f"Found {len(rows)} dangling DrefFile record(s) (images+photos+direct_fk):")
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
        self.stdout.write("\n-- Moving dangling rows to tmp_dref_dreffile_combined --")
        id_list_sql = ",".join(str(i) for i in dangling_ids)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tmp_dref_dreffile_combined (LIKE dref_dreffile INCLUDING ALL);
                TRUNCATE TABLE tmp_dref_dreffile_combined;
                INSERT INTO tmp_dref_dreffile_combined SELECT * FROM dref_dreffile WHERE id IN ("""
                + id_list_sql
                + ");"
            )
            cursor.execute("DELETE FROM dref_dreffile WHERE id IN (" + id_list_sql + ")")
        self.stdout.write(f"Moved {len(dangling_ids)} rows to tmp_dref_dreffile_combined and deleted originals.")

    def _print_stats(self, stats_row, dangling_count=None):
        (
            total_files,
            total_referenced_unique,
            images_link_rows,
            photos_link_rows,
            direct_fk_rows,
            dangling_estimate,
        ) = stats_row
        if dangling_count is None:
            dangling_count = dangling_estimate
        used_pct = (total_referenced_unique / total_files * 100.0) if total_files else 0.0
        dangling_pct = (dangling_count / total_files * 100.0) if total_files else 0.0
        self.stdout.write("\n=== DrefFile Usage Stats (images + photos + direct FK) ===")
        self.stdout.write(f"Total files: {total_files}")
        self.stdout.write(
            f"Referenced (unique across all image/photo/direct FK relations): {total_referenced_unique} ({used_pct:.2f}%)"
        )
        self.stdout.write(f"Dangling: {dangling_count} ({dangling_pct:.2f}%)")
        self.stdout.write("Breakdown (raw relation row counts):")
        self.stdout.write(f"  Images link rows total: {images_link_rows}")
        self.stdout.write(f"  Photos link rows total: {photos_link_rows}")
        self.stdout.write(f"  Direct FK rows total: {direct_fk_rows}")
