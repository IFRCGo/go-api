from django.test import TestCase

from dref.dref3_common import Dref3Stage, build_branch_filters
from dref.dref3_query import UNION_COLUMNS, _branch, get_excluded_codes


class Dref3UnionAlignmentTests(TestCase):
    """UNION ALL aligns columns positionally: every branch must compile to
    the exact same SELECT shape, or rows silently get scrambled."""

    def test_branch_columns_are_aligned(self):
        branch_filters = build_branch_filters({})
        shapes = []
        for stage in Dref3Stage:
            qs = _branch(stage, branch_filters[stage], None, get_excluded_codes())
            values_select = tuple(qs.query.values_select)
            annotations = tuple(qs.query.annotation_select.keys())
            self.assertEqual(set(values_select) | set(annotations), set(UNION_COLUMNS))
            shapes.append((values_select, annotations))
        # identical concrete-field order and annotation order across branches
        self.assertEqual(len(set(shapes)), 1, f"Branch SELECT shapes diverge: {shapes}")
