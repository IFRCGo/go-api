"""UNION-queryset builder for the /api/v2/dref3/ endpoint.

Builds one aligned `.values()` queryset per stage model, applies every
filter *before* the union (union querysets don't support filter/annotate),
then combines with UNION ALL. The result supports count(), order_by on the
output columns and slicing — everything DRF's LimitOffsetPagination needs.
"""

from django.db.models import (
    DateTimeField,
    IntegerField,
    Min,
    OuterRef,
    Q,
    Subquery,
    Value,
)
from django.db.models.functions import Upper

from dref.dref3_common import (
    Dref3AccessFilter,
    Dref3Stage,
    build_branch_filters,
    build_ordering,
    get_excluded_codes,
    has_full_access,
    ordering_needs_group_first,
    parse_stage_filter,
)
from dref.models import Dref, DrefFinalReport, DrefOperationalUpdate

# Output columns of every union branch. All three branches are built by the
# same code path with identical concrete-field/annotation names, so the
# compiled SELECT column order is consistent across branches (union aligns
# positionally). Never diverge one branch's shape from the others.
BASE_UNION_COLUMNS = ("id", "stage", "appeal_code", "created_at")
GROUP_FIRST_COLUMN = "group_first_created_at"
UNION_COLUMNS = (*BASE_UNION_COLUMNS, GROUP_FIRST_COLUMN)


def union_columns(include_group_first: bool) -> tuple[str, ...]:
    return UNION_COLUMNS if include_group_first else BASE_UNION_COLUMNS


_STAGE_MODELS = {
    Dref3Stage.APPLICATION: Dref,
    Dref3Stage.OPERATIONAL_UPDATE: DrefOperationalUpdate,
    Dref3Stage.FINAL_REPORT: DrefFinalReport,
}


def _group_first_created_at_subquery():
    """Min(created_at) of the appeal_code's application rows (NULL if none)."""
    return Subquery(
        Dref.objects.filter(appeal_code=OuterRef("appeal_code"))
        .order_by()
        .values("appeal_code")
        .annotate(m=Min("created_at"))
        .values("m")[:1],
        output_field=DateTimeField(null=True),
    )


def _branch(stage: Dref3Stage, branch_q: Q, user, excluded_codes, access, include_group_first):
    model = _STAGE_MODELS[stage]
    qs = model.objects.exclude(appeal_code__isnull=True).exclude(appeal_code="")

    if not has_full_access(user):
        qs = qs.filter(status=Dref.Status.APPROVED)
        if excluded_codes:
            qs = qs.annotate(_uc=Upper("appeal_code")).exclude(_uc__in=excluded_codes)
    else:
        # Non-superuser "DREF3 Admins": same per-source-model narrowing the
        # legacy endpoint applied, but intersected so it cannot discard the
        # filters below (no-op for superusers).
        qs = access.narrow(qs)

    annotations = {"stage": Value(stage.value, output_field=IntegerField())}
    if include_group_first:
        annotations[GROUP_FIRST_COLUMN] = _group_first_created_at_subquery()

    return qs.filter(branch_q).order_by().annotate(**annotations).values(*union_columns(include_group_first))


def empty_union_queryset(include_group_first: bool = True):
    annotations = {"stage": Value(Dref3Stage.APPLICATION.value, output_field=IntegerField())}
    if include_group_first:
        annotations[GROUP_FIRST_COLUMN] = _group_first_created_at_subquery()
    return Dref.objects.none().annotate(**annotations).values(*union_columns(include_group_first))


def build_union_queryset(user, query_params, access: Dref3AccessFilter | None = None):
    """Single filtered+ordered UNION ALL queryset for the requesting user.

    Raises dref3_common.EmptyResult when params provably match nothing.
    Pass the same `access` instance to Dref3PageHydrator to compute the
    user-access narrowing once per request instead of twice.
    """
    branch_filters = build_branch_filters(query_params)  # may raise EmptyResult
    excluded_codes = get_excluded_codes()
    access = access or Dref3AccessFilter(user)

    # The correlated Min() subquery behind group_first_created_at costs one
    # scan of dref_dref per output row, so only select it when the requested
    # ordering actually reads it.
    include_group_first = ordering_needs_group_first(query_params.get("order_by"))

    stages = parse_stage_filter(query_params.get("stage"))
    branches = [
        _branch(stage, branch_q, user, excluded_codes, access, include_group_first)
        for stage, branch_q in branch_filters.items()
        if stages is None or stage in stages
    ]

    if len(branches) == 1:
        union = branches[0]  # plain values queryset; same interface
    else:
        union = branches[0].union(*branches[1:], all=True)

    return union.order_by(*build_ordering(query_params.get("order_by")))
