import importlib

from main.test_case import APITestCase

from deployments.factories.project import ProjectFactory
from deployments.models import SectorTags, Project


class TestCustomMigrationsLogic(APITestCase):
    # TODO: This is a temporary test for PR only, after merging we will remove this (and also RCCE from SectorTags).
    def test_remove_rcce_tag(self):
        migration_file = importlib.import_module('deployments.migrations.0039_auto_20210823_1159')
        project_0 = ProjectFactory.create(secondary_sectors=[])  # Without any RCCE tag
        project_1 = ProjectFactory.create(secondary_sectors=[SectorTags.RCCE]) # Without just RCCE tag
        project_2 = ProjectFactory.create(   # With RCCE tag + other tags
            secondary_sectors=[SectorTags.RCCE, SectorTags.MIGRATION, SectorTags.WASH]
        )
        project_3 = ProjectFactory.create(  # With other tags
            secondary_sectors=[SectorTags.MIGRATION, SectorTags.WASH]
        )
        project_4 = ProjectFactory.create(  # With RCCE + CEA and HEALTH_PUBLIC
            secondary_sectors=[SectorTags.RCCE, SectorTags.HEALTH_PUBLIC, SectorTags.CEA]
        )
        project_5 = ProjectFactory.create(  # With RCCE + CEA
            secondary_sectors=[SectorTags.RCCE, SectorTags.CEA]
        )
        # Apply the migration logic
        migration_file._remove_rcce_tag(Project)

        project_0.refresh_from_db()
        project_1.refresh_from_db()
        project_2.refresh_from_db()
        project_3.refresh_from_db()
        project_4.refresh_from_db()
        project_5.refresh_from_db()

        assert set(project_0.secondary_sectors) == set([])
        assert set(project_1.secondary_sectors) == set([SectorTags.HEALTH_PUBLIC, SectorTags.CEA])
        assert set(
            project_2.secondary_sectors
        ) == set([SectorTags.HEALTH_PUBLIC, SectorTags.CEA, SectorTags.MIGRATION, SectorTags.WASH])
        assert set(project_3.secondary_sectors) == set([SectorTags.MIGRATION, SectorTags.WASH])
        assert set(project_4.secondary_sectors) == set([SectorTags.HEALTH_PUBLIC, SectorTags.CEA])
        assert set(project_5.secondary_sectors) == set([SectorTags.HEALTH_PUBLIC, SectorTags.CEA])
