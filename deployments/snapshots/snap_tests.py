# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestProjectAPI::test_project_list_one 1'] = b'{"count":0,"next":null,"previous":null,"results":[]}'

snapshots['TestProjectAPI::test_project_list_zero 1'] = b'{"count":0,"next":null,"previous":null,"results":[]}'
