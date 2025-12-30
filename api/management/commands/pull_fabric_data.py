import time
from typing import Any

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from api.fabric_import_map import FABRIC_IMPORT_STAGES, FABRIC_DB, FABRIC_SCHEMA
from api.fabric_sql import fetch_all


DEFAULT_APP_LABEL = "api"  # <-- change if your Fabric models live in another Django app


class Command(BaseCommand):
    help = "One-time pull of Fabric tables into Postgres (staged, chunked)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--only",
            nargs="*",
            help="Optional list of stage slugs to run (e.g. dim-appeal dim-product).",
        )
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=10000,
            help="Rows per batch to fetch from Fabric (default: 250).",
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

    def _row_to_model_kwargs(self, model_cls, row):
        """
        Convert a Fabric row dict into kwargs for creating a Django model instance.

        - Never populate Django's surrogate PK (`id`)
        - Map Fabric's `id` column to `fabric_id` when present
        - Drop any extra/helper columns (e.g. rn)
        """
        kwargs = {}

        model_fields = {f.name: f for f in model_cls._meta.concrete_fields}

        for col, value in row.items():
            # Ignore helper columns
            if col == "rn":
                continue

            # Map Fabric `id` → Django `fabric_id`
            if col == "id" and "fabric_id" in model_fields:
                kwargs["fabric_id"] = value
                continue

            # Never manually set Django PK
            if col == "id" and model_fields["id"].primary_key:
                continue

            # Normal field copy if it exists on the model
            if col in model_fields:
                kwargs[col] = value

        return kwargs


    def handle(self, *args, **options):
        only = set(options["only"] or [])
        chunk_size = int(options["chunk_size"])
        no_truncate = bool(options["no_truncate"])

        stages = [s for s in FABRIC_IMPORT_STAGES if not only or s["slug"] in only]
        self.stdout.write(self.style.SUCCESS(f"Starting pull_fabric_data: {len(stages)} stages"))

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

            # Optional quick sanity check
            t0 = time.time()
            test_sql = f"SELECT TOP (1) * FROM {fq_table}"
            _ = fetch_all(test_sql, limit=1)
            self.stdout.write(self.style.SUCCESS(f"  [TEST] Fabric reachable ({time.time() - t0:.2f}s)"))

            # Truncate local table once per stage (recommended for one-time loads)
            if not no_truncate:
                self.stdout.write("  Truncating local table...")
                with transaction.atomic():
                    self._truncate_model_table(model_cls)
                self.stdout.write(self.style.SUCCESS("  Truncate OK"))

            total_inserted = 0
            batch_num = 0
            stage_start = time.time()

            if pagination == "keyset":
                last_val = None
                while True:
                    if last_val is None:
                        sql = f"""
                            SELECT TOP ({chunk_size}) *
                            FROM {fq_table}
                            ORDER BY [{page_key}] ASC
                        """
                        rows = fetch_all(sql, limit=chunk_size)
                    else:
                        sql = f"""
                            SELECT TOP ({chunk_size}) *
                            FROM {fq_table}
                            WHERE [{page_key}] > ?
                            ORDER BY [{page_key}] ASC
                        """
                        rows = fetch_all(sql, params=(last_val,), limit=chunk_size)

                    if not rows:
                        break

                    # Build model objects from row dicts
                    objs = []
                    for r in rows:
                        r.pop("rn", None)  # just in case
                        kwargs = self._row_to_model_kwargs(model_cls, r)
                        objs.append(model_cls(**kwargs))

                    # Insert chunk
                    with transaction.atomic():
                        model_cls.objects.bulk_create(objs, batch_size=chunk_size, ignore_conflicts=True) # <-- skips duplicates of the PK because in our case all duplicates are identical

                    batch_num += 1
                    total_inserted += len(objs)
                    last_val = rows[-1][page_key]

                    self.stdout.write(self.style.SUCCESS(
                        f"  [BATCH {batch_num}] inserted {len(objs)} (total={total_inserted}) last_{page_key}={last_val}"
                    ))

            elif pagination == "row_number":
                # Note: row_number recomputes each time; acceptable for one-off imports.
                last_rn = 0
                while True:
                    start_rn = last_rn + 1
                    end_rn = last_rn + chunk_size

                    sql = f"""
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
                    rows = fetch_all(sql, params=(start_rn, end_rn), limit=chunk_size)

                    if not rows:
                        break

                    objs = []
                    for r in rows:
                        r.pop("rn", None)  # remove helper column
                        kwargs = self._row_to_model_kwargs(model_cls, r)
                        objs.append(model_cls(**kwargs))

                    with transaction.atomic():
                        model_cls.objects.bulk_create(objs, batch_size=chunk_size, ignore_conflicts=True) # <-- skips duplicates of the PK because in our case all duplicates are identical

                    batch_num += 1
                    total_inserted += len(objs)
                    last_rn = end_rn

                    self.stdout.write(self.style.SUCCESS(
                        f"  [BATCH {batch_num}] inserted {len(objs)} (total={total_inserted}) rn={start_rn}..{end_rn}"
                    ))

                    if len(rows) < chunk_size:
                        break
            else:
                raise RuntimeError(f"Unknown pagination mode '{pagination}' for stage '{slug}'")

            self.stdout.write(self.style.SUCCESS(
                f"  Stage complete: {slug} inserted={total_inserted} time={time.time() - stage_start:.2f}s"
            ))

        self.stdout.write(self.style.SUCCESS("\nDone."))