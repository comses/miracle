from .common import BaseMiracleTest
from ..models import (Dataset, DataTable, DataTableColumn)

"""
Miracle core metadata app model tests
"""


class ProjectDatasetMetadataTest(BaseMiracleTest):

    def test_blank_names(self):
        try:
            self.create_project(name='')
            self.fail("Should not have been able to create a project with a blank name")
        except:
            pass
        try:
            Dataset.objects.create(project=self.default_project, creator=self.default_user)
            self.fail("Should not have been able to create a dataset with a blank name")
        except:
            pass

    def test_slugs(self):
        project = self.default_project
        self.assertTrue(project.slug)
        dataset = Dataset.objects.create(project=project, name='Test Miracle Dataset', creator=self.default_user)
        self.assertTrue(dataset.slug)
