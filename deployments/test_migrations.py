import importlib

from main.test_case import APITestCase

from deployments.factories.project import ProjectFactory
from deployments.models import SectorTags, Project


class TestCustomMigrationsLogic(APITestCase):
    """
    Test for testing the custom migrations logic
    Skip the test if migrations is removed
    """

    def test_remove_rcce_tag(self):
        migration_file = importlib.import_module('deployments.migrations.0039_auto_20210823_1159')

        project_1 = ProjectFactory.create(secondary_sectors=[SectorTags.RCCE])
        project_2 = ProjectFactory.create(secondary_sectors=[SectorTags.RCCE, SectorTags.MIGRATION, SectorTags.WASH])

        # Apply the migration logic
        migration_file._remove_rcce_tag(Project)

        assert set(Project.objects.filter(id=project_1.id).values_list('secondary_sectors', flat=True)[0])\
            == set([SectorTags.HEALTH_PUBLIC, SectorTags.CEA])
        assert set(Project.objects.filter(id=project_2.id).values_list('secondary_sectors', flat=True)[0])\
            == set([SectorTags.HEALTH_PUBLIC, SectorTags.CEA, SectorTags.MIGRATION, SectorTags.WASH])
