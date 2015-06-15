from .common import BaseMiracleTest, logger
from ..models import (Project, Dataset, DataTable, DataTableColumn, DatasetConnectionMixin, Group)
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


class ProjectGroupMembershipTest(BaseMiracleTest):

    def test_project_group(self):
        project = self.default_project
        group = project.get_group()
        self.assertTrue(group)
        self.assertEqual(group.name, project.group_name)
        self.assertEqual(Group.objects.get(name=project.group_name), group)

    def test_group_membership(self):
        users = [self.create_user(username='testuser' + str(i)) for i in xrange(0, 15)]
        project = self.default_project
        for user in users:
            self.assertFalse(project.has_group_member(user))
            project.add_group_member(user)
            self.assertTrue(project.has_group_member(user))

        second_group = [self.create_user(username='externaltestuser' + str(i)) for i in xrange(0, 15)]
        for user in second_group:
            self.assertFalse(project.has_group_member(user))


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


class BookmarkedProjectTest(BaseMiracleTest):

    def test_bookmarks(self):
        # check default user bookmark
        project = self.default_project
        user = self.default_user
        self.assertFalse(user.bookmarked_projects.exists())
        project.bookmark_for(user)
        self.assertEqual(user.bookmarked_projects.all()[0].project, project)
        self.assertEqual(user.bookmarked_projects.count(), 1)

        second_user = self.create_user(username='secondtestuser')
        second_project = self.create_project(name='second test project')
        self.assertFalse(second_user.bookmarked_projects.exists())
        second_project.bookmark_for(second_user)
        # second bookmarked project should not affect first
        self.assertEqual(user.bookmarked_projects.count(), 1)
        self.assertEqual(user.bookmarked_projects.all()[0].project, project)
        self.assertEqual(second_user.bookmarked_projects.all()[0].project, second_project)
        self.assertEqual(second_user.bookmarked_projects.count(), 1)
