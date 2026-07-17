"""Shared building blocks for the /api/v2/dref3/ endpoint.

This module is intentionally identical in the `dref3-umbrella` and
`dref3-union` branches so the two implementations only differ in how the
single row-queryset is produced (denormalized table vs UNION query).

A "row" is one instance of Dref / DrefOperationalUpdate / DrefFinalReport,
identified by (stage, pk, appeal_code). The queryset layer (approach
specific) is responsible for filtering / ordering / pagination over row
identities; the `Dref3PageHydrator` here turns a page of row identities back
into the exact response payloads the legacy endpoint produced, by fetching
the full appeal-code groups and reusing the existing Dref3 serializers.
"""

import csv

from django.db import models
from django.db.models import F, Q
from django.http import HttpResponse

# NOTE: dref.models imports Dref3Stage from this module, so all dref/api model
# imports here must stay function-local to avoid an import cycle.


class Dref3Stage(models.IntegerChoices):
    APPLICATION = 1, "Application"
    OPERATIONAL_UPDATE = 2, "Operational Update"
    FINAL_REPORT = 3, "Final Report"


STAGE_BY_MODEL_NAME = {
    "Dref": Dref3Stage.APPLICATION,
    "DrefOperationalUpdate": Dref3Stage.OPERATIONAL_UPDATE,
    "DrefFinalReport": Dref3Stage.FINAL_REPORT,
}


def stage_models():
    from dref.models import Dref, DrefFinalReport, DrefOperationalUpdate

    return {
        Dref3Stage.APPLICATION: Dref,
        Dref3Stage.OPERATIONAL_UPDATE: DrefOperationalUpdate,
        Dref3Stage.FINAL_REPORT: DrefFinalReport,
    }


# -- Legacy param parsing -----------------------------------------------------

_STAGE_ALIASES = {
    "application": Dref3Stage.APPLICATION,
    "app": Dref3Stage.APPLICATION,
    "dref": Dref3Stage.APPLICATION,
    "operational_update": Dref3Stage.OPERATIONAL_UPDATE,
    "operationalupdate": Dref3Stage.OPERATIONAL_UPDATE,
    "op_update": Dref3Stage.OPERATIONAL_UPDATE,
    "op": Dref3Stage.OPERATIONAL_UPDATE,
    "update": Dref3Stage.OPERATIONAL_UPDATE,
    "final_report": Dref3Stage.FINAL_REPORT,
    "finalreport": Dref3Stage.FINAL_REPORT,
    "final": Dref3Stage.FINAL_REPORT,
    "report": Dref3Stage.FINAL_REPORT,
}


def parse_stage_filter(raw) -> set[Dref3Stage] | None:
    """Canonical stages from a comma-separated, case-insensitive alias list."""
    if not raw:
        return None
    stages = {
        _STAGE_ALIASES[key]
        for part in str(raw).split(",")
        if (key := part.strip().lower()) in _STAGE_ALIASES
    }
    return stages or None


def status_to_int(raw):
    from dref.models import Dref

    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        pass
    label_map = {s.label.lower(): s.value for s in Dref.Status}
    name_map = {s.name.lower(): s.value for s in Dref.Status}
    return label_map.get(str(raw).lower()) or name_map.get(str(raw).lower())


def parse_composite_ids(raw) -> dict[Dref3Stage, set[int]] | None:
    """Parse ?id=Dref-3,DrefOperationalUpdate-7 into per-stage pk sets.

    Returns None when the param is absent/empty (no filtering). A present
    param with no valid tokens yields an empty mapping (=> empty result),
    matching the legacy behavior of matching tokens against row ids.
    """
    if raw is None or str(raw).strip() == "":
        return None
    wanted: dict[Dref3Stage, set[int]] = {}
    for token in str(raw).split(","):
        token = token.strip()
        model_name, _, pk = token.rpartition("-")
        stage = STAGE_BY_MODEL_NAME.get(model_name)
        if stage is None or not pk.isdigit():
            continue
        wanted.setdefault(stage, set()).add(int(pk))
    return wanted


def get_excluded_codes() -> set[str]:
    """Appeal codes hidden from non-admin users (uppercased)."""
    from api.models import AppealFilter

    try:
        values = AppealFilter.objects.filter(name="ingestAppealFilter").values_list("value", flat=True)
        raw = values[0].split(",") if values.count() > 0 else []
    except Exception:
        # If model/app not available, fail open (no extra exclusions)
        return set()
    return {c.strip().upper() for c in raw if c.strip()}


def has_full_access(user) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return user.groups.filter(name="DREF3 Admins").exists()


def resolve_appeal_id(raw) -> str | None:
    """Resolve ?appeal_id=<pk> to an appeal_code (legacy probe order)."""
    try:
        pk = int(raw)
    except (TypeError, ValueError):
        return None
    for model in stage_models().values():
        obj = model.objects.filter(pk=pk).only("appeal_code").first()
        if obj and obj.appeal_code:
            return obj.appeal_code
    return None


# -- Declarative filter mapping ----------------------------------------------
# param -> (coerce, per-stage source-model lookups). A `None` lookup means the
# filter does not constrain that stage's rows. Approach A translates these to
# Dref3Row columns/joins; approach B applies them per union branch.

def _coerce_int(raw):
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _coerce_iso3(raw):
    return raw.strip().upper() if raw else None


# Date-range filters that were dead code in the legacy endpoint, now applied
# for real. They constrain application-stage rows only (other stages pass).
# NOTE: hazard_date_and_location is a TextField; __gte/__lte compare
# lexicographically, mirroring what the legacy code intended to do.
DREF3_APPLICATION_RANGE_FIELDS = (
    "event_date",
    "ns_respond_date",
    "government_requested_assistance_date",
    "ns_request_date",
    "submission_to_geneva",
    "date_of_approval",
    "publishing_date",
    "hazard_date_and_location",
    "end_date",
)

DREF3_FILTERS = {
    "appeal_code_prefix": (
        str,
        ("appeal_code__startswith", "appeal_code__startswith", "appeal_code__startswith"),
    ),
    "region": (
        _coerce_int,
        ("national_society__region_id", "national_society__region_id", "national_society__region_id"),
    ),
    "country_iso3": (
        _coerce_iso3,
        ("national_society__iso3__iexact", "national_society__iso3__iexact", "national_society__iso3__iexact"),
    ),
    "appeal_type": (
        _coerce_int,
        ("type_of_dref", "dref__type_of_dref", "dref__type_of_dref"),
    ),
    "operation_status": (
        status_to_int,
        ("status", "status", "status"),
    ),
    "start_date_of_operation": (
        str,
        ("date_of_approval__gte", "new_operational_start_date__gte", "operation_start_date__gte"),
    ),
    "end_date_of_operation": (
        str,
        ("end_date__lte", "new_operational_end_date__lte", "operation_end_date__lte"),
    ),
    **{
        f"{field}_{suffix}": (
            str,
            (f"{field}__{op}", None, None),
        )
        for field in DREF3_APPLICATION_RANGE_FIELDS
        for suffix, op in (("from", "gte"), ("to", "lte"))
    },
}


class EmptyResult(Exception):
    """Raised while building filters when the result is provably empty."""


def build_branch_filters(query_params) -> dict[Dref3Stage, Q]:
    """Build one Q object per stage from legacy query params.

    Raises EmptyResult when a param invalidates everything (e.g. an
    ?appeal_id= that resolves to no appeal_code).
    """
    branch_q = {stage: Q() for stage in Dref3Stage}

    for param, (coerce, lookups) in DREF3_FILTERS.items():
        raw = query_params.get(param)
        if raw is None or raw == "":
            continue
        value = coerce(raw)
        if value is None:
            continue  # legacy behavior: unparseable values are ignored
        for stage, lookup in zip(Dref3Stage, lookups):
            if lookup is not None:
                branch_q[stage] &= Q(**{lookup: value})

    appeal_id = query_params.get("appeal_id")
    if appeal_id:
        code = resolve_appeal_id(appeal_id)
        if code is None:
            raise EmptyResult
        for stage in Dref3Stage:
            branch_q[stage] &= Q(appeal_code=code)

    wanted_ids = parse_composite_ids(query_params.get("id"))
    if wanted_ids is not None:
        for stage in Dref3Stage:
            branch_q[stage] &= Q(pk__in=sorted(wanted_ids.get(stage, ())))

    return branch_q


# -- Ordering ------------------------------------------------------------------
# Both approaches expose the same column names on their row queryset:
#   id, stage, appeal_code, created_at, group_first_created_at
# where group_first_created_at = Min(created_at) of the group's application
# rows (NULL when the appeal_code has no application row -> sorts last, like
# the legacy `_order_codes`).

DREF3_ORDER_COLUMNS = ("appeal_code", "stage", "created_at", "id")


def build_ordering(order_by: str | None) -> list:
    tail = list(DREF3_ORDER_COLUMNS)
    if order_by == "created_at":
        return [F("group_first_created_at").asc(nulls_last=True), *tail]
    if order_by == "-created_at":
        return [F("group_first_created_at").desc(nulls_last=True), *tail]
    return tail


# -- Page hydration ------------------------------------------------------------

_ALLOCATION_ORDINALS = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth"]

_HYDRATE_SELECT_RELATED = ("country",)
_HYDRATE_PREFETCH_RELATED = (
    "planned_interventions",
    "district",
    "country__region",
    "disaster_type",
)


class Dref3PageHydrator:
    """Turn an ordered page of (stage, pk, appeal_code) row identities into
    serialized response rows, reproducing the legacy group-context fields
    (stage label numbering, allocation ordinals, is_latest_stage, public).

    Group context is computed over the instances *visible to the requesting
    user* (light users only see APPROVED), exactly like the legacy
    handle_retrieve path. Cost is bounded: 3 pk-independent group queries +
    prefetches + 1 Appeal query per page, regardless of page size.
    """

    def __init__(self, user):
        self.user = user
        self.full_access = has_full_access(user)
        self.excluded_codes = get_excluded_codes()

    def _visible_group_querysets(self, codes):
        # Late imports: dref.views/dref.models import this module.
        from dref.models import Dref
        from dref.views import filter_dref_queryset_by_user_access

        global_filters: dict = {"appeal_code__in": list(codes)}
        if not self.full_access:
            global_filters["status"] = Dref.Status.APPROVED
            global_filters["appeal_code__in"] = [c for c in codes if c and c.upper() not in self.excluded_codes]
            if not global_filters["appeal_code__in"]:
                return []

        querysets = [
            model.objects.filter(**global_filters)
            .select_related(*_HYDRATE_SELECT_RELATED)
            .prefetch_related(*_HYDRATE_PREFETCH_RELATED)
            .order_by("created_at")
            for model in stage_models().values()
        ]
        if self.full_access:
            querysets = [filter_dref_queryset_by_user_access(self.user, qs) for qs in querysets]
        return querysets

    def fetch_groups(self, codes) -> dict[str, list]:
        """appeal_code -> stage-major, created_at-ordered visible instances."""
        groups: dict[str, list] = {}
        for queryset in self._visible_group_querysets(codes):
            for item in queryset:
                groups.setdefault(item.appeal_code, []).append(item)
        return groups

    def serialize_group(self, code, instances, prefetched_appeal_by_code) -> list[tuple[tuple[int, int], dict]]:
        # Local imports to avoid import cycles at app loading time.
        from dref.models import Dref, DrefFinalReport, DrefOperationalUpdate
        from dref.serializers import (
            Dref3Serializer,
            DrefFinalReport3Serializer,
            DrefOperationalUpdate3Serializer,
        )

        ops_update_count = 0
        allocation_count = 1  # Dref Application is always the first allocation
        public = code not in self.excluded_codes

        # is_latest_stage: last APPROVED instance with no APPROVED successor
        latest_index = None
        for i, inst in enumerate(instances):
            if getattr(inst, "status", None) == Dref.Status.APPROVED:
                next_inst = instances[i + 1] if i + 1 < len(instances) else None
                if next_inst is None or getattr(next_inst, "status", None) != Dref.Status.APPROVED:
                    latest_index = i

        rows = []
        for i, instance in enumerate(instances):
            context = {
                "public": public,
                "is_latest_stage": i == latest_index,
                "prefetched_appeal_by_code": prefetched_appeal_by_code,
            }
            if isinstance(instance, Dref):
                stage = Dref3Stage.APPLICATION
                serializer = Dref3Serializer(
                    instance,
                    context={**context, "stage": "Application", "allocation": _ALLOCATION_ORDINALS[0]},
                )
            elif isinstance(instance, DrefOperationalUpdate):
                stage = Dref3Stage.OPERATIONAL_UPDATE
                ops_update_count += 1
                if instance.additional_allocation and len(_ALLOCATION_ORDINALS) > allocation_count:
                    allocation = _ALLOCATION_ORDINALS[allocation_count]
                    allocation_count += 1
                else:
                    allocation = "No allocation"
                serializer = DrefOperationalUpdate3Serializer(
                    instance,
                    context={**context, "stage": f"Operational Update {ops_update_count}", "allocation": allocation},
                )
            elif isinstance(instance, DrefFinalReport):
                stage = Dref3Stage.FINAL_REPORT
                serializer = DrefFinalReport3Serializer(
                    instance,
                    context={**context, "stage": "Final Report", "allocation": "No allocation"},
                )
            else:
                continue
            rows.append(((stage.value, instance.pk), serializer.data))
        return rows

    def hydrate(self, page_rows) -> list[dict]:
        """page_rows: ordered iterable of (stage:int, pk:int, appeal_code:str)."""
        from api.models import Appeal

        page_rows = list(page_rows)
        codes = {code for _, _, code in page_rows}
        if not codes:
            return []
        groups = self.fetch_groups(codes)
        prefetched_appeal_by_code = {
            appeal.code: appeal for appeal in Appeal.objects.only("code", "event_id").filter(code__in=codes)
        }
        serialized: dict[tuple[int, int], dict] = {}
        for code, instances in groups.items():
            for key, data in self.serialize_group(code, instances, prefetched_appeal_by_code):
                serialized[key] = data
        return [serialized[(stage, pk)] for stage, pk, _ in page_rows if (stage, pk) in serialized]

    def hydrate_codes(self, codes) -> list[dict]:
        """Legacy retrieve() path: all visible rows for the given codes."""
        from api.models import Appeal

        groups = self.fetch_groups(codes)
        prefetched_appeal_by_code = {
            appeal.code: appeal for appeal in Appeal.objects.only("code", "event_id").filter(code__in=list(codes))
        }
        return [
            data
            for code, instances in groups.items()
            for _, data in self.serialize_group(code, instances, prefetched_appeal_by_code)
        ]


# -- CSV export ------------------------------------------------------------------


def dref3_csv_response(rows) -> HttpResponse:
    header, seen = [], set()
    rows = list(rows)
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                header.append(key)
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="dref3_export.csv"'
    writer = csv.writer(resp)
    writer.writerow(header)
    for row in rows:
        writer.writerow([row.get(k, "") for k in header])
    return resp
