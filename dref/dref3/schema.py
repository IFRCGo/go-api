"""OpenAPI query parameters for the /api/v2/dref3/ endpoint.

The filter parameters are *generated* from `DREF3_FILTERS`, the same mapping
`query.py` applies, so the documented parameters cannot drift from the ones
actually honoured: adding a filter there documents it here automatically.
Only the parameters handled outside that mapping (`stage`, `appeal_id`, `id`,
`order_by`, `export`) are listed by hand.

`filter_backends` is empty on the viewset because all filtering happens before
the union, so drf-spectacular has no FilterSet to introspect - hence this
module.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

from dref.dref3.common import (
    DREF3_FILTERS,
    Dref3Stage,
    coerce_date_str,
    coerce_int,
    coerce_iso3,
    status_to_int,
)
from dref.models import Dref

# Coercer -> documented type. Keyed by the callable itself so a filter that
# changes its coercer changes its documented type with it.
_TYPE_BY_COERCER = {
    coerce_int: OpenApiTypes.INT,
    coerce_iso3: OpenApiTypes.STR,
    coerce_date_str: OpenApiTypes.DATE,
    status_to_int: OpenApiTypes.STR,
    str: OpenApiTypes.STR,
}


def _choice_list(choices) -> str:
    """Render `value label` pairs straight from the model's choices.

    Never hand-write these: the ids are not alphabetical or otherwise
    guessable (DrefType is 0 Imminent, 1 Assessment, 2 Response, 3 Loan), and
    a stale copy here would be served to clients as fact.
    """
    return ", ".join(f"`{choice.value}` {choice.label}" for choice in choices)


_DESCRIPTIONS = {
    "appeal_code_prefix": "Rows whose `appeal_code` starts with this value (case-sensitive).",
    "region": "Region id of the national society.",
    "country_iso3": "ISO3 country code of the national society (case-insensitive).",
    "appeal_type": f"DREF type (`type_of_dref`): {_choice_list(Dref.DrefType)}.",
    "operation_status": (
        f"Status as an id, label or name ({_choice_list(Dref.Status)}), e.g. `4` or `Approved`. "
        "Unrecognised values are ignored."
    ),
    "start_date_of_operation": (
        "Lower bound (inclusive) on each stage's own start date: `date_of_approval` for applications, "
        "`new_operational_start_date` for operational updates, `operation_start_date` for final reports."
    ),
    "end_date_of_operation": (
        "Upper bound (inclusive) on each stage's own end date: `end_date` for applications, "
        "`new_operational_end_date` for operational updates, `operation_end_date` for final reports."
    ),
}

# Params whose accepted values are a closed set, documented as a real enum.
# `operation_status` is deliberately absent: it also accepts labels and names,
# so an enum of ids would misdescribe it.
_ENUMS = {
    "appeal_type": [choice.value for choice in Dref.DrefType],
}


def _range_description(param: str) -> str:
    field, _, bound = param.rpartition("_")
    edge = "Lower" if bound == "from" else "Upper"
    if field == "hazard_date_and_location":
        # TextField: compared lexicographically, not as a date.
        return f"{edge} bound on `{field}`, compared as text rather than as a date."
    return f"{edge} bound (inclusive) on `{field}`."


def _stage_note(lookups) -> str:
    """Say which stages a filter narrows, when it does not narrow all three."""
    applies = [stage for stage, lookup in zip(Dref3Stage, lookups) if lookup is not None]
    if len(applies) == len(Dref3Stage):
        return ""
    if not applies:
        return " Currently has no effect."
    labels = ", ".join(Dref3Stage(stage).label for stage in applies)
    return f" Constrains {labels} rows only; rows of other stages are unaffected."


def _describe(param: str, lookups) -> str:
    base = _DESCRIPTIONS.get(param) or _range_description(param)
    return base + _stage_note(lookups)


def _filter_parameters():
    for param, (coerce, lookups) in DREF3_FILTERS.items():
        yield OpenApiParameter(
            name=param,
            type=_TYPE_BY_COERCER.get(coerce, OpenApiTypes.STR),
            location=OpenApiParameter.QUERY,
            required=False,
            description=_describe(param, lookups),
            enum=_ENUMS.get(param),
        )


_STAGE_PARAMETERS = [
    OpenApiParameter(
        name="stage",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        description=(
            "Comma-separated list of stages to include. Case-insensitive, accepts aliases: "
            "`application`/`app`/`dref`, `operational_update`/`operationalupdate`/`op_update`/`op`/`update`, "
            "`final_report`/`finalreport`/`final`/`report`. Unknown tokens are ignored; "
            "if none are recognised the filter is not applied."
        ),
    ),
    OpenApiParameter(
        name="appeal_id",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        required=False,
        description=(
            "Primary key of a Dref, DrefOperationalUpdate or DrefFinalReport (probed in that order). "
            "Resolved to that record's `appeal_code` and applied as an appeal_code filter, so it returns "
            "the whole group. A pk that resolves to no appeal_code yields an empty result."
        ),
    ),
    OpenApiParameter(
        name="id",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        description=(
            "Comma-separated composite row ids as returned in the `id` field, "
            "e.g. `Dref-6,DrefOperationalUpdate-4,DrefFinalReport-1`. "
            "Malformed tokens are ignored; a present param matching nothing yields an empty result."
        ),
    ),
    OpenApiParameter(
        name="order_by",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        description=(
            "Use `created_at` or `-created_at` to order row groups by the first DREF application "
            "created_at per appeal_code; any other value defaults to appeal_code ordering. "
            "Rows of one appeal_code always stay contiguous (stage-major, then created_at)."
        ),
    ),
    OpenApiParameter(
        name="export",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        enum=["csv"],
        description="`csv` streams the full filtered set as a CSV attachment, bypassing pagination.",
    ),
]

# Filters first (in DREF3_FILTERS order), then the hand-written parameters.
# SORT_OPERATION_PARAMETERS is False, so this order is what the schema shows.
DREF3_LIST_PARAMETERS = [*_filter_parameters(), *_STAGE_PARAMETERS]
