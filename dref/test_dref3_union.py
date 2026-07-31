from django.test import TestCase

from dref.dref3_common import Dref3AccessFilter, Dref3Stage, build_branch_filters
from dref.dref3_query import (
    BASE_UNION_COLUMNS,
    GROUP_FIRST_COLUMN,
    UNION_COLUMNS,
    _branch,
    build_union_queryset,
    get_excluded_codes,
)


class Dref3UnionAlignmentTests(TestCase):
    """UNION ALL aligns columns positionally: every branch must compile to
    the exact same SELECT shape, or rows silently get scrambled."""

    def _shapes(self, include_group_first):
        branch_filters = build_branch_filters({})
        access = Dref3AccessFilter(None)
        shapes = []
        expected = set(UNION_COLUMNS if include_group_first else BASE_UNION_COLUMNS)
        for stage in Dref3Stage:
            qs = _branch(
                stage,
                branch_filters[stage],
                None,
                get_excluded_codes(),
                access,
                include_group_first,
            )
            values_select = tuple(qs.query.values_select)
            annotations = tuple(qs.query.annotation_select.keys())
            self.assertEqual(set(values_select) | set(annotations), expected)
            shapes.append((values_select, annotations))
        return shapes

    def test_branch_columns_are_aligned(self):
        shapes = self._shapes(include_group_first=True)
        # identical concrete-field order and annotation order across branches
        self.assertEqual(len(set(shapes)), 1, f"Branch SELECT shapes diverge: {shapes}")

    def test_branch_columns_are_aligned_without_group_first(self):
        """The cheaper shape (no correlated Min() subquery) must align too."""
        shapes = self._shapes(include_group_first=False)
        self.assertEqual(len(set(shapes)), 1, f"Branch SELECT shapes diverge: {shapes}")

    def test_group_first_subquery_only_selected_when_ordering_needs_it(self):
        """The correlated Min() subquery costs a dref_dref scan per output row,
        so it must not be selected for orderings that never read it."""
        for params, expected in (
            ({}, False),
            ({"order_by": "appeal_code"}, False),
            ({"order_by": "bogus"}, False),
            ({"order_by": "created_at"}, True),
            ({"order_by": "-created_at"}, True),
        ):
            with self.subTest(params=params):
                sql = str(build_union_queryset(None, params).query)
                self.assertEqual(GROUP_FIRST_COLUMN in sql, expected)
