"""Shared building blocks for the /api/v2/dref3/ endpoint.

A "row" is one instance of Dref / DrefOperationalUpdate / DrefFinalReport,
identified by (stage, pk, appeal_code). `query.py` is responsible for
filtering / ordering / pagination over row identities; the
`Dref3PageHydrator` here turns a page of row identities back into the exact
response payloads the legacy endpoint produced, by fetching the full
appeal-code groups and reusing the Dref3 serializers.
"""

import csv
import io
import itertools
import logging

from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Upper
from django.http import StreamingHttpResponse

# Model and serializer imports are function-local throughout this module, so
# importing it never pulls in the app registry at import time.

logger = logging.getLogger(__name__)


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
    stages = {_STAGE_ALIASES[key] for part in str(raw).split(",") if (key := part.strip().lower()) in _STAGE_ALIASES}
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
        # `str.isdigit()` is also True for non-ASCII digits (e.g. "²") that
        # int() cannot parse, so require ASCII to keep int() total here.
        if stage is None or not (pk.isascii() and pk.isdigit()):
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
# filter does not constrain that stage's rows. `query.py` applies these per
# union branch, before the union.


def coerce_int(raw):
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def coerce_iso3(raw):
    return raw.strip().upper() if raw else None


def coerce_date_str(raw):
    """Validate a YYYY-MM-DD date param, returning the original string.

    The value is passed through unchanged (not as a `date`) so the generated
    SQL stays byte-identical to before this guard existed. Anything Django
    cannot parse is dropped -> the filter is ignored, consistent with every
    other coercer here. Without this, an unparseable value reaches
    `queryset.filter(<DateField>__gte=...)`, which raises Django's
    ValidationError from deep inside the ORM -> HTTP 500 instead of a result.
    """
    from django.utils.dateparse import parse_date

    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        if parse_date(text) is None:
            return None
    except ValueError:
        # Well-formed but impossible dates, e.g. 2024-13-01.
        return None
    return text


def coerce_search_term(raw):
    """A non-blank search term, or None so the filter is ignored.

    A blank term would reach `__icontains` as the empty string, which every row
    with a value matches - a filter that silently narrows nothing. A missing
    value is dropped here rather than by the caller, because `str(None)` is the
    non-blank "None", which would otherwise be searched for verbatim.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


# Date-range filters, exposed as `<field>_from` / `<field>_to`. They constrain
# application-stage rows only (other stages pass). Every field here is a
# DateField: `hazard_date` answers "when is the hazard expected to happen?",
# which the free-text `hazard_date_and_location` only describes in prose.
DREF3_APPLICATION_RANGE_FIELDS = (
    "event_date",
    "ns_respond_date",
    "government_requested_assistance_date",
    "ns_request_date",
    "submission_to_geneva",
    "date_of_approval",
    "publishing_date",
    "hazard_date",
    "end_date",
)

DREF3_FILTERS = {
    "appeal_code_prefix": (
        str,
        ("appeal_code__startswith", "appeal_code__startswith", "appeal_code__startswith"),
    ),
    "region": (
        coerce_int,
        ("national_society__region_id", "national_society__region_id", "national_society__region_id"),
    ),
    "country_iso3": (
        coerce_iso3,
        ("national_society__iso3__iexact", "national_society__iso3__iexact", "national_society__iso3__iexact"),
    ),
    "appeal_type": (
        coerce_int,
        ("type_of_dref", "dref__type_of_dref", "dref__type_of_dref"),
    ),
    "operation_status": (
        status_to_int,
        ("status", "status", "status"),
    ),
    # Free text ("when and where is the hazard expected to happen?"), so it is
    # searched for a substring. Only the application stage has the field.
    "hazard_date_and_location": (
        coerce_search_term,
        ("hazard_date_and_location__icontains", None, None),
    ),
    "start_date_of_operation": (
        coerce_date_str,
        ("date_of_approval__gte", "new_operational_start_date__gte", "operation_start_date__gte"),
    ),
    "end_date_of_operation": (
        coerce_date_str,
        ("end_date__lte", "new_operational_end_date__lte", "operation_end_date__lte"),
    ),
    **{
        f"{field}_{suffix}": (
            coerce_date_str,
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


def ordering_needs_group_first(order_by: str | None) -> bool:
    """Whether the requested ordering reads `group_first_created_at`.

    Only `order_by=±created_at` does. Every other request can skip the
    correlated Min() subquery that computes it entirely.
    """
    return order_by in ("created_at", "-created_at")


def build_ordering(order_by: str | None) -> list:
    tail = list(DREF3_ORDER_COLUMNS)
    if order_by == "created_at":
        return [F("group_first_created_at").asc(nulls_last=True), *tail]
    if order_by == "-created_at":
        return [F("group_first_created_at").desc(nulls_last=True), *tail]
    return tail


# -- User-access narrowing -----------------------------------------------------


class Dref3AccessFilter:
    """Per-request user-access narrowing for the three stage models.

    `dref.views.filter_dref_queryset_by_user_access` *replaces* the queryset
    with `model.get_for(user)` for an authenticated user who is neither a
    superuser nor a regional admin, which silently discards the caller's own
    filters, ordering, `select_related` and `prefetch_related`. Intersect on
    the pk set instead, so a caller's queryset keeps its own shape.

    The per-model access queryset is built once per request and reused as a
    SQL subquery: `DrefOperationalUpdate.get_for` / `DrefFinalReport.get_for`
    run `dref.utils.get_dref_users()` (a full Dref scan plus a Python loop) at
    *construction* time, so caching the object is what avoids repeating it in
    both the query phase and the hydrate phase.
    """

    def __init__(self, user):
        self.user = user
        self._access_qs: dict[type, models.QuerySet | None] = {}

    def _access_queryset(self, model):
        if model not in self._access_qs:
            from dref.views import filter_dref_queryset_by_user_access

            if getattr(self.user, "is_superuser", False):
                self._access_qs[model] = None  # unrestricted
            else:
                self._access_qs[model] = filter_dref_queryset_by_user_access(self.user, model.objects.all())
        return self._access_qs[model]

    def narrow(self, queryset):
        """Restrict `queryset` to rows the user may access, preserving it."""
        access_qs = self._access_queryset(queryset.model)
        if access_qs is None:
            return queryset
        return queryset.filter(id__in=access_qs.values("id"))


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

    def __init__(self, user, access: "Dref3AccessFilter | None" = None):
        self.user = user
        self.full_access = has_full_access(user)
        self.excluded_codes = get_excluded_codes()
        # Share one instance with the queryset builder to avoid recomputing the
        # per-model access narrowing (see Dref3AccessFilter).
        self.access = access or Dref3AccessFilter(user)

    def _visible_group_querysets(self, codes):
        # Late imports: dref.views/dref.models import this module.
        from dref.models import Dref

        codes = [c for c in codes if c]
        if not codes:
            return []

        querysets = [
            model.objects.filter(appeal_code__in=codes)
            .select_related(*_HYDRATE_SELECT_RELATED)
            .prefetch_related(*_HYDRATE_PREFETCH_RELATED)
            .order_by("created_at")
            for model in stage_models().values()
        ]
        if not self.full_access:
            # Exclude embargoed codes in SQL with the *same* expression the
            # queryset layer uses, so the two phases can never disagree and
            # silently return fewer rows than `count` advertises. (Postgres
            # upper() and Python str.upper() differ on some non-ASCII input.)
            querysets = [qs.filter(status=Dref.Status.APPROVED) for qs in querysets]
            if self.excluded_codes:
                querysets = [qs.annotate(_uc=Upper("appeal_code")).exclude(_uc__in=self.excluded_codes) for qs in querysets]
        else:
            querysets = [self.access.narrow(qs) for qs in querysets]
        return querysets

    def fetch_groups(self, codes) -> dict[str, list]:
        """appeal_code -> stage-major, created_at-ordered visible instances."""
        groups: dict[str, list] = {}
        for queryset in self._visible_group_querysets(codes):
            for item in queryset:
                groups.setdefault(item.appeal_code, []).append(item)
        return groups

    def _stage_serializers(self):
        """One serializer per stage, reused for every row of the page.

        DRF deep-copies all declared fields on each serializer instance's first
        `.fields` access, so instantiating one per row costs ~95
        Field.__deepcopy__ calls per row - the dominant cost of this endpoint.
        The fields are identical for every row, so build them once and vary only
        the context and the instance passed to `to_representation`.

        Cached on the hydrator (one per request), deliberately not module-level:
        `_context` is mutable per-row state, so a shared instance would let
        concurrent requests interleave one row's group context into another's.
        """
        if not hasattr(self, "_stage_serializer_cache"):
            # Local imports to avoid import cycles at app loading time.
            from dref.dref3.serializers import (
                Dref3Serializer,
                DrefFinalReport3Serializer,
                DrefOperationalUpdate3Serializer,
            )

            self._stage_serializer_cache = {
                Dref3Stage.APPLICATION: Dref3Serializer(),
                Dref3Stage.OPERATIONAL_UPDATE: DrefOperationalUpdate3Serializer(),
                Dref3Stage.FINAL_REPORT: DrefFinalReport3Serializer(),
            }
        return self._stage_serializer_cache

    def serialize_group(self, code, instances, prefetched_appeal_by_code) -> list[tuple[tuple[int, int], dict]]:
        # Local imports to avoid import cycles at app loading time.
        from dref.models import Dref, DrefFinalReport, DrefOperationalUpdate

        ops_update_count = 0
        allocation_count = 1  # Dref Application is always the first allocation
        # `excluded_codes` is uppercased, and the row-visibility filters above
        # compare against it uppercased too - so this must as well, or a
        # mixed-case appeal_code would be hidden from light users while still
        # being reported as public to the admins who can see it.
        public = (code or "").upper() not in self.excluded_codes

        # is_latest_stage: last APPROVED instance with no APPROVED successor
        latest_index = None
        for i, inst in enumerate(instances):
            if getattr(inst, "status", None) == Dref.Status.APPROVED:
                next_inst = instances[i + 1] if i + 1 < len(instances) else None
                if next_inst is None or getattr(next_inst, "status", None) != Dref.Status.APPROVED:
                    latest_index = i

        serializers_by_stage = self._stage_serializers()
        rows = []
        for i, instance in enumerate(instances):
            context = {
                "public": public,
                "is_latest_stage": i == latest_index,
                "prefetched_appeal_by_code": prefetched_appeal_by_code,
            }
            if isinstance(instance, Dref):
                stage = Dref3Stage.APPLICATION
                context.update(stage="Application", allocation=_ALLOCATION_ORDINALS[0])
            elif isinstance(instance, DrefOperationalUpdate):
                stage = Dref3Stage.OPERATIONAL_UPDATE
                ops_update_count += 1
                if instance.additional_allocation and len(_ALLOCATION_ORDINALS) > allocation_count:
                    allocation = _ALLOCATION_ORDINALS[allocation_count]
                    allocation_count += 1
                else:
                    allocation = "No allocation"
                context.update(stage=f"Operational Update {ops_update_count}", allocation=allocation)
            elif isinstance(instance, DrefFinalReport):
                stage = Dref3Stage.FINAL_REPORT
                context.update(stage="Final Report", allocation="No allocation")
            else:
                continue
            serializer = serializers_by_stage[stage]
            # DRF resolves Field.context through self.root._context, so
            # reassigning it re-points the shared serializer at this row.
            serializer._context = context
            # `.data` memoizes into `_data`, which on a reused serializer would
            # pin the first row's output onto every later row.
            rows.append(((stage.value, instance.pk), serializer.to_representation(instance)))
        return rows

    def _appeal_map(self, groups) -> dict:
        """Appeal-by-code map covering every code that will be serialized.

        Keyed off the fetched groups rather than the requested codes: the
        serializers treat a present map as authoritative (no per-row fallback
        query), so a map narrower than the rows being serialized would silently
        yield null `link_to_emergency_page` values.
        """
        from api.models import Appeal

        codes = [code for code in groups if code]
        if not codes:
            return {}
        return {appeal.code: appeal for appeal in Appeal.objects.only("code", "event_id").filter(code__in=codes)}

    def _serialize_groups(self, groups) -> dict[tuple[int, int], dict]:
        prefetched_appeal_by_code = self._appeal_map(groups)
        serialized: dict[tuple[int, int], dict] = {}
        for code, instances in groups.items():
            for key, data in self.serialize_group(code, instances, prefetched_appeal_by_code):
                serialized[key] = data
        return serialized

    def hydrate(self, page_rows) -> list[dict]:
        """page_rows: ordered iterable of (stage:int, pk:int, appeal_code:str)."""
        page_rows = list(page_rows)
        codes = {code for _, _, code in page_rows}
        if not codes:
            return []
        serialized = self._serialize_groups(self.fetch_groups(codes))
        rows = [serialized[(stage, pk)] for stage, pk, _ in page_rows if (stage, pk) in serialized]
        if len(rows) != len(page_rows):
            # The row query and the group query are separate round-trips, so a
            # concurrent delete/status change can drop a row after it was
            # counted. Never silent: `count`/`next` still advertise the total.
            missing = [(stage, pk) for stage, pk, _ in page_rows if (stage, pk) not in serialized]
            logger.warning(
                "dref3: %d of %d page rows vanished between the row query and hydration: %s",
                len(missing),
                len(page_rows),
                missing[:20],
            )
        return rows

    def hydrate_codes(self, codes) -> list[dict]:
        """Legacy retrieve() path: all visible rows for the given codes."""
        groups = self.fetch_groups(codes)
        prefetched_appeal_by_code = self._appeal_map(groups)
        return [
            data
            for code, instances in groups.items()
            for _, data in self.serialize_group(code, instances, prefetched_appeal_by_code)
        ]


# -- CSV export ------------------------------------------------------------------


# The export is unpaginated by design, so it must never materialize the whole
# result set: hydrate a chunk of rows at a time and stream it out.
DREF3_CSV_CHUNK_SIZE = 500


def dref3_csv_header() -> list[str]:
    """Column order for the export.

    All three Dref3 serializers share one `Meta.fields` list, so this is the
    same header the previous implementation derived by unioning the keys of
    every serialized row - without needing every row in memory first.
    """
    from dref.dref3.serializers import Dref3Serializer

    return list(Dref3Serializer.Meta.fields)


def dref3_csv_streaming_response(row_identities, hydrate) -> StreamingHttpResponse:
    """Stream the export, hydrating `DREF3_CSV_CHUNK_SIZE` rows at a time.

    `hydrate` fetches the complete appeal-code group for each chunk, so group
    context (stage numbering, allocation ordinals, is_latest_stage) is computed
    exactly as it is for a single page; a code spanning two chunks is fetched
    twice but still emits only its own rows, in queryset order.
    """
    header = dref3_csv_header()

    def content():
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        def flush():
            data = buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            return data

        writer.writerow(header)
        yield flush()

        rows = iter(row_identities)
        while chunk := list(itertools.islice(rows, DREF3_CSV_CHUNK_SIZE)):
            for row in hydrate(chunk):
                writer.writerow([row.get(key, "") for key in header])
            yield flush()

    resp = StreamingHttpResponse(content(), content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="dref3_export.csv"'
    return resp
