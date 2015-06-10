from .common import BaseMiracleTest, logger
from ..models import (Dataset, DataTable, DataTableColumn, DatasetConnectionMixin)
import string

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
        "lots of spaces towards the end?                ",
        "?!?!@#!@#!@#!#&)!@#!@#@#!@#!@#!%&)&)&(*!)(#!#!@#http://www.postgresql.org/docs/9.4/static/sql-syntax-lexical.html#SQL-SYNTAX-IDENTIFIERS",
        ")(*&&^%$#@!\w",
        "normal",
        u'ko\u017eu\u0161\u010dek',
    )

    data_types = [dt[0] for dt in DataTableColumn.DataType]

    def test_datatable_column_identifiers(self):
        dataset = self.default_project.datasets.create(name='Test Miracle Dataset')
        number_of_data_types = len(self.data_types)
        for identifier in self.test_identifiers:
            datatable = dataset.tables.create(name=identifier)
            self.assertEqual(datatable.name, identifier)
            for i in xrange(0, 15):
                column_name = 'Column ' + string.ascii_uppercase[i]
                data_type = self.data_types[i % number_of_data_types]
                column = datatable.columns.create(name=column_name, data_type=data_type)
                self.assertEqual(column.name, column_name)
            # identifier sanitization only happens when create_schema is explicitly invoked
            datatable.create_schema()
            sanitized_identifier = datatable.name
            self.assertTrue(sanitized_identifier[0].isalpha())
            self.assertTrue(len(sanitized_identifier) <= DatasetConnectionMixin.MAX_NAME_LENGTH)
            # full_name should have original identifier
            self.assertEqual(datatable.full_name, identifier)
            logger.debug("sanitized identifier: %s", sanitized_identifier)
            # all child columns should also be sanitized as well
            for i in xrange(0, 15):
                column_name = 'Column ' + string.ascii_uppercase[i]
                column = datatable.columns.get(full_name=column_name)
                self.assertEqual(column.data_type, self.data_types[i % number_of_data_types])
