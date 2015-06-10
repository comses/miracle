from .common import BaseMiracleTest, logger
from ..models import (Dataset, DataTable, DataTableColumn, DatasetConnectionMixin)

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

    test_identifiers = (
        ' this is a very long, harrowing name...111!!!111 and how. ',
        " good gravy! it's a space kaiser! ",
        "lots of spaces towards the end?  ",
        "?!?!@#!@#!@#!#&)!@#!@#@#!@#!@#!%&)&)&(*!)(#!#!@#http://www.postgresql.org/docs/9.4/static/sql-syntax-lexical.html#SQL-SYNTAX-IDENTIFIERS",
        ")(*&&^%$#@!\w",
        "normal",
        u'ko\u017eu\u0161\u010dek',
    )

    def test_datatable_column_identifiers(self):
        dataset = self.default_project.datasets.create(name='Test Miracle Dataset')
        for identifier in self.test_identifiers:
            datatable = dataset.tables.create(name=identifier)
            sanitized_identifier = datatable.name
            self.assertTrue(sanitized_identifier[0].isalpha())
            self.assertTrue(len(sanitized_identifier) <= DatasetConnectionMixin.MAX_NAME_LENGTH)
            logger.debug("sanitized identifier: %s", sanitized_identifier)
            self.assertEqual(datatable.full_name, identifier)
            column = datatable.columns.create(name='Column A', data_type=DataTableColumn.DataType.bigint)
            self.assertEqual(datatable.columns.count(), 1)
            self.assertEqual(datatable.columns.get(full_name='Column A'), column)
            self.assertEqual(datatable.columns.get(name__contains='column_a'), column)
            datatable.columns.create(name='Column B', data_type=DataTableColumn.DataType.boolean)
            self.assertEqual(datatable.columns.count(), 2)
            datatable.columns.create(name='Column C', data_type=DataTableColumn.DataType.text)
