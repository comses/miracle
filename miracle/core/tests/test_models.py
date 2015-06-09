from .common import BaseMiracleTest, logger
from ..models import (Dataset, DataTable, DataTableColumn)

"""
Miracle core metadata app model tests
"""


class MetadataTest(BaseMiracleTest):

    def test_blank_names(self):
        """
        Do not allow blank names in Projects, Datasets, DataTables, or DataTableColumns
        """
        try:
            self.create_project(name='')
            self.fail("Allowed empty Project.name")
        except:
            pass
        try:
            self.default_project.datasets.create('')
            self.fail("Allowed empty Dataset.name")
        except:
            pass
        dataset = self.default_project.datasets.create(name='Test Dataset')
        try:
            dataset.tables.create(name='')
            self.fail("Allowed empty DataTable.name")
        except:
            pass
        datatable = dataset.tables.create(name='Tabular Table')
        try:
            datatable.columns.create(name='')
            self.fail("Allowed empty DataTableColumn.name")
        except:
            pass

    def test_slugs(self):
        project = self.default_project
        self.assertTrue(project.slug)
        dataset = project.datasets.create(name='Test Miracle Dataset', creator=self.default_user)
        self.assertTrue(dataset.slug)


class DatasetTest(BaseMiracleTest):

    def test_create_datatable_schema(self):
        dataset = self.default_project.datasets.create(name='Test Miracle Dataset')
        datatable = dataset.tables.create(name='Tabular Table')
        column = datatable.columns.create(name='Column A', data_type=DataTableColumn.DataType.bigint)
        self.assertEqual(datatable.columns.count(), 1)
        self.assertEqual(datatable.columns.get(name='Column A'), column)
        datatable.columns.create(name='Column B', data_type=DataTableColumn.DataType.boolean)
        self.assertEqual(datatable.columns.count(), 2)
        datatable.columns.create(name='Column C', data_type=DataTableColumn.DataType.text)
