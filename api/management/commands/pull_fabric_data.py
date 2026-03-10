import hashlib
import time
import uuid
from datetime import datetime

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

from api.fabric_import_map import FABRIC_DB, FABRIC_IMPORT_STAGES, FABRIC_SCHEMA
from api.fabric_sql import fetch_all, get_fabric_connection

DEFAULT_APP_LABEL = "api"

# --------------------------------------------------------------------------- #
# Staging-table helpers                                                        #
# --------------------------------------------------------------------------- #

# Rows per INSERT statement – keeps us well under psycopg2's 65 535 param limit.
_STAGING_INSERT_BATCH = 2000

# Stable lock key derived from the command name.  All Postgres sessions running
# this command share the same slot so concurrent cron invocations are detected.
_ADVISORY_LOCK_KEY = int(hashlib.md5(b"pull_fabric_data").hexdigest()[:16], 16) & 0x7FFFFFFFFFFFFFFF


def _acquire_advisory_lock() -> bool:
    """
    Try to acquire a Postgres session-level advisory lock.
    Returns True if the lock was acquired, False if another session holds it.
    The lock is automatically released when the process (session) exits.
    """
    with connection.cursor() as cur:
        cur.execute("SELECT pg_try_advisory_lock(%s)", [_ADVISORY_LOCK_KEY])
        return bool(cur.fetchone()[0])


def _release_advisory_lock() -> None:
    with connection.cursor() as cur:
        cur.execute("SELECT pg_advisory_unlock(%s)", [_ADVISORY_LOCK_KEY])


def _create_staging_table(live_table: str, run_id: str) -> str:
    """
    Create a fresh, uniquely named staging table for this run.
    The name embeds *run_id* (short UUID hex) so concurrent cron runs cannot
    collide or truncate each other's in-progress data.
    No indexes or FK constraints are copied so bulk loads stay fast.
    Returns the staging table name.
    """
    staging = f"{live_table}_stg_{run_id}"
    with connection.cursor() as cur:
        cur.execute(f'CREATE TABLE "{staging}" (LIKE "{live_table}" INCLUDING DEFAULTS)')
    return staging


def _build_insertable_fields(model_cls, pk_name: str) -> list:
    """
    Return the concrete fields that should be inserted explicitly.
    Auto-generated PK fields are excluded so the sequence fills them in.
    """
    _AUTO_PK_TYPES = {"AutoField", "BigAutoField", "SmallAutoField"}
    return [f for f in model_cls._meta.concrete_fields if not (f.name == pk_name and f.__class__.__name__ in _AUTO_PK_TYPES)]


def _bulk_insert_staging(staging_table: str, insertable_fields: list, objs: list) -> int:
    """
    Insert *objs* (Django model instances) into *staging_table* via raw SQL.
    Uses sub-batches of *_STAGING_INSERT_BATCH* rows to stay within psycopg2's
    parameter limit.  Returns the total number of rows inserted.
    """
    if not objs:
        return 0

    col_str = ", ".join(f'"{f.column}"' for f in insertable_fields)
    row_tpl = "(" + ", ".join(["%s"] * len(insertable_fields)) + ")"
    inserted = 0

    with connection.cursor() as cur:
        for start in range(0, len(objs), _STAGING_INSERT_BATCH):
            sub_batch = objs[start : start + _STAGING_INSERT_BATCH]
            flat_values: list = []
            for obj in sub_batch:
                for f in insertable_fields:
                    flat_values.append(getattr(obj, f.attname))
            value_rows = ", ".join([row_tpl] * len(sub_batch))
            cur.execute(
                f'INSERT INTO "{staging_table}" ({col_str}) VALUES {value_rows}',
                flat_values,
            )
            inserted += len(sub_batch)

    return inserted


def _atomic_live_swap(live_table: str, staging_table: str, insertable_fields: list) -> None:
    """
    Replace live table contents atomically with the staging table contents.

    Within a single transaction:
      1. TRUNCATE the live table  — ACCESS EXCLUSIVE lock held for the txn duration.
      2. INSERT INTO live (col1, col2, …) SELECT col1, col2, … FROM staging.

    An explicit column list is used so the swap is correct regardless of any
    column-order difference between the two tables.

    With READ COMMITTED isolation (Postgres default), readers queue behind the
    ACCESS EXCLUSIVE lock and see the fully populated table once the txn commits.
    They will never observe an empty or partially filled table.
    """
    col_str = ", ".join(f'"{f.column}"' for f in insertable_fields)
    with transaction.atomic():
        with connection.cursor() as cur:
            cur.execute(f'TRUNCATE TABLE "{live_table}" CASCADE')
            cur.execute(f'INSERT INTO "{live_table}" ({col_str}) ' f'SELECT {col_str} FROM "{staging_table}"')


def _merge_staging_into_live(live_table: str, staging_table: str, insertable_fields: list) -> None:
    """
    Insert staging rows into the live table, skipping rows that would violate
    a PK or unique constraint.  Mirrors the original ``ignore_conflicts=True``
    behaviour used with ``--no-truncate``.  An explicit column list is used so
    the merge is correct regardless of column-order differences.
    """
    col_str = ", ".join(f'"{f.column}"' for f in insertable_fields)
    with transaction.atomic():
        with connection.cursor() as cur:
            cur.execute(
                f'INSERT INTO "{live_table}" ({col_str}) ' f'SELECT {col_str} FROM "{staging_table}" ON CONFLICT DO NOTHING'
            )


def _drop_staging_table(staging_table: str) -> None:
    with connection.cursor() as cur:
        cur.execute(f'DROP TABLE IF EXISTS "{staging_table}"')


class Command(BaseCommand):
    help = "One-time pull of Fabric tables into Postgres (staged, chunked)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--only",
            nargs="*",
            help="Optional list of stage slugs to run (e.g. dim-appeal dim-product).",
        )
        parser.add_argument(
            "--exclude",
            nargs="*",
            help="Optional list of stage slugs to skip (e.g. dim-appeal).",
        )
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=10000,
            help="Rows per batch to fetch from Fabric (default: 10000).",
        )
        parser.add_argument(
            "--no-truncate",
            action="store_true",
            help="Do not truncate local tables before inserting (default is truncate+insert).",
        )

    def _resolve_model(self, stage: dict) -> type:
        """
        Resolve model class from stage. Supports:
          - stage["model"] = "DimAppeal" + stage["app_label"] (or DEFAULT_APP_LABEL)
          - stage["model"] = "someapp.DimAppeal"
        """
        model_ref = stage["model"]

        if "." in model_ref:
            app_label, model_name = model_ref.split(".", 1)
        else:
            app_label = stage.get("app_label", DEFAULT_APP_LABEL)
            model_name = model_ref

        model_cls = apps.get_model(app_label, model_name)
        if model_cls is None:
            raise RuntimeError(f"Could not resolve model '{model_ref}' (app_label='{app_label}')")
        return model_cls

    def _truncate_model_table(self, model_cls: type):
        """
        TRUNCATE the underlying Postgres table for the model.
        Uses CASCADE to avoid FK issues in staging DB imports.
        """
        table = model_cls._meta.db_table
        with connection.cursor() as cur:
            cur.execute(f'TRUNCATE TABLE "{table}" CASCADE;')

    def _row_to_model_kwargs(self, row, model_fields, pk_name, pk_field):
        """
        Convert a Fabric row dict into kwargs for creating a Django model instance.

        Rules:
        - Never populate Django's surrogate PK (`id`) if it's an AutoField/BigAutoField
        - If Fabric provides `id` and model has `fabric_id`, map Fabric `id` -> `fabric_id`
        - Normalize blank strings to None
        - Drop helper columns (rn)
        """
        kwargs = {}

        def norm(v):
            # Treat empty/whitespace strings as None
            if isinstance(v, str):
                v = v.strip()
                if v == "":
                    return None
            return v

        for col, value in row.items():
            if col == "rn":
                continue

            value = norm(value)

            # Fabric `id` -> Django `fabric_id` (if present)
            if col == "id" and "fabric_id" in model_fields:
                kwargs["fabric_id"] = value
                continue

            # Never write to surrogate PK if it's auto-created
            if col == pk_name and pk_field is not None:
                internal_auto_types = {"AutoField", "BigAutoField", "SmallAutoField"}
                if pk_field.__class__.__name__ in internal_auto_types:
                    continue

            if col in model_fields:
                field = model_fields[col]
                internal = field.get_internal_type()

                # DateField: Fabric returns datetime at midnight -> store date only
                # If the model field is a DateField but Fabric gave incorrectly us a datetime, drop the time part
                # Specifically affects DimLineAgreement, DimTransactionLine, DimItemBatch,
                # DimPackingSlipLine, DimSalesOrderLine, DimVendorPhysicalAddress, FctProductReceipt
                if internal == "DateField" and isinstance(value, datetime):
                    value = value.date()

                # DateTimeField: Fabric returns naive datetime -> store as UTC-aware
                elif internal == "DateTimeField" and isinstance(value, datetime) and timezone.is_naive(value):
                    value = timezone.make_aware(value, timezone=timezone.utc)

                kwargs[col] = value

        return kwargs

    def handle(self, *args, **options):
        only = set(options["only"] or [])
        exclude = set(options["exclude"] or [])
        chunk_size = int(options["chunk_size"])
        no_truncate = bool(options["no_truncate"])

        if not _acquire_advisory_lock():
            self.stdout.write(
                self.style.ERROR(
                    "Another pull_fabric_data run is already in progress "
                    f"(advisory lock key {_ADVISORY_LOCK_KEY}). Exiting safely."
                )
            )
            return
        # The session-level advisory lock auto-releases when this process exits.
        # An explicit _release_advisory_lock() call is not required for cron safety.
        run_id = uuid.uuid4().hex[:12]

        stages = [s for s in FABRIC_IMPORT_STAGES if (not only or s["slug"] in only) and s["slug"] not in exclude]
        self.stdout.write(self.style.SUCCESS(f"Starting pull_fabric_data: {len(stages)} stages (run_id={run_id})"))

        # Verify Fabric connectivity once before processing any stages
        t0 = time.time()
        conn = get_fabric_connection()
        cursor = conn.cursor()
        first_table = stages[0]["table"] if stages else None
        if first_table:
            test_fq = f"[{FABRIC_DB}].[{FABRIC_SCHEMA}].[{first_table}]"
            _ = fetch_all(cursor, f"SELECT TOP (1) * FROM {test_fq}", limit=1)
            self.stdout.write(self.style.SUCCESS(f"[TEST] Fabric reachable ({time.time() - t0:.2f}s)"))

        for idx, stage in enumerate(stages, start=1):
            slug = stage["slug"]
            table = stage["table"]
            page_key = stage.get("page_key")
            pagination = stage.get("pagination", "keyset")

            if not page_key:
                raise RuntimeError(f"Stage '{slug}' is missing 'page_key'")

            fq_table = f"[{FABRIC_DB}].[{FABRIC_SCHEMA}].[{table}]"

            model_cls = self._resolve_model(stage)
            self.stdout.write(f"\n[{idx}/{len(stages)}] Stage: {slug}")
            self.stdout.write(f"  Fabric table: {fq_table}")
            self.stdout.write(f"  Target model: {model_cls.__module__}.{model_cls.__name__}")
            self.stdout.write(f"  Pagination: {pagination} | page_key: {page_key} | chunk_size: {chunk_size}")

            model_fields = {f.name: f for f in model_cls._meta.concrete_fields}
            pk_name = model_cls._meta.pk.name
            pk_field = model_fields.get(pk_name)
            has_fabric_id = "fabric_id" in model_fields
            insertable_fields = _build_insertable_fields(model_cls, pk_name)

            # ---------------------------------------------------------------- #
            # Prepare staging table — live table is NOT touched at this point.  #
            # ---------------------------------------------------------------- #
            live_table = model_cls._meta.db_table
            staging_table = _create_staging_table(live_table, run_id)
            self.stdout.write(self.style.SUCCESS(f"  Staging table '{staging_table}' created — loading '{slug}'..."))

            total_inserted = 0
            batch_num = 0
            stage_start = time.time()

            try:
                if pagination == "keyset":
                    sql_initial = f"""
                        SELECT TOP ({chunk_size}) *
                        FROM {fq_table}
                        ORDER BY [{page_key}] ASC
                    """
                    sql_keyset = f"""
                        SELECT TOP ({chunk_size}) *
                        FROM {fq_table}
                        WHERE [{page_key}] > ?
                        ORDER BY [{page_key}] ASC
                    """
                    last_val = None
                    objs = []
                    while True:
                        if last_val is None:
                            rows = fetch_all(cursor, sql_initial, limit=chunk_size)
                        else:
                            rows = fetch_all(cursor, sql_keyset, params=(last_val,), limit=chunk_size)

                        if not rows:
                            break

                        objs.clear()
                        for r in rows:
                            r.pop("rn", None)
                            kwargs = self._row_to_model_kwargs(r, model_fields, pk_name, pk_field)

                            if has_fabric_id:
                                if not kwargs.get("fabric_id"):
                                    continue

                            objs.append(model_cls(**kwargs))

                        n = _bulk_insert_staging(staging_table, insertable_fields, objs)
                        batch_num += 1
                        total_inserted += n
                        last_val = rows[-1][page_key]

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  [BATCH {batch_num}] staged {n} rows to '{staging_table}' "
                                f"(total={total_inserted}) last_{page_key}={last_val}"
                            )
                        )

                elif pagination == "row_number":
                    sql_rn = f"""
                        WITH numbered AS (
                            SELECT
                                *,
                                ROW_NUMBER() OVER (ORDER BY [{page_key}] ASC) AS rn
                            FROM {fq_table}
                        )
                        SELECT *
                        FROM numbered
                        WHERE rn BETWEEN ? AND ?
                        ORDER BY rn ASC
                    """
                    last_rn = 0
                    objs = []
                    while True:
                        start_rn = last_rn + 1
                        end_rn = last_rn + chunk_size

                        rows = fetch_all(cursor, sql_rn, params=(start_rn, end_rn), limit=chunk_size)

                        if not rows:
                            break

                        objs.clear()
                        for r in rows:
                            r.pop("rn", None)
                            kwargs = self._row_to_model_kwargs(r, model_fields, pk_name, pk_field)

                            if has_fabric_id:
                                if not kwargs.get("fabric_id"):
                                    continue

                            objs.append(model_cls(**kwargs))

                        n = _bulk_insert_staging(staging_table, insertable_fields, objs)
                        batch_num += 1
                        total_inserted += n
                        last_rn = end_rn

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  [BATCH {batch_num}] staged {n} rows to '{staging_table}' "
                                f"(total={total_inserted}) rn={start_rn}..{end_rn}"
                            )
                        )

                        if len(rows) < chunk_size:
                            break

                else:
                    raise RuntimeError(f"Unknown pagination mode '{pagination}' for stage '{slug}'")

            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"  [ROLLBACK] Stage '{slug}' failed during staging load: {exc}\n"
                        f"  Live table '{live_table}' is unchanged. "
                        f"Staging table '{staging_table}' preserved for inspection."
                    )
                )
                raise
            finally:
                # Always close Fabric cursor and connection regardless of outcome.
                cursor.close()
                conn.close()

            # ---------------------------------------------------------------- #
            # Atomically push staged data into the live table.                  #
            # Only reached when all batches completed without error.            #
            # ---------------------------------------------------------------- #
            self.stdout.write(f"  [SWAP START] '{staging_table}' ({total_inserted} rows) -> '{live_table}'")
            try:
                if no_truncate:
                    _merge_staging_into_live(live_table, staging_table, insertable_fields)
                    self.stdout.write(self.style.SUCCESS(f"  [SWAP SUCCESS] '{live_table}' updated (merge, no truncate)"))
                else:
                    _atomic_live_swap(live_table, staging_table, insertable_fields)
                    self.stdout.write(self.style.SUCCESS(f"  [SWAP SUCCESS] '{live_table}' fully replaced from staging"))
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"  [SWAP FAIL] Swap failed for '{slug}': {exc}\n"
                        f"  Staging table '{staging_table}' preserved for manual recovery."
                    )
                )
                raise

            _drop_staging_table(staging_table)
            self.stdout.write(self.style.SUCCESS(f"  Staging table '{staging_table}' dropped"))

            self.stdout.write(
                self.style.SUCCESS(f"  Stage complete: {slug} inserted={total_inserted} time={time.time() - stage_start:.2f}s")
            )

        self.stdout.write(self.style.SUCCESS("\nDone."))
