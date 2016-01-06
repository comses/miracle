from django.core.exceptions import ValidationError
from .common import BaseMiracleTest, logger
from ..models import (DataColumn, Group, Project, AnalysisParameter)
import string

"""
Miracle core metadata app model tests
"""


class MetadataTest(BaseMiracleTest):

    def test_blank_names(self):
        """
        Do not allow blank names in Projects, Datasets, DataTables, or DataColumn
        """
        project = self.default_project
        with self.assertRaises(ValidationError):
            self.create_project(name='')
        with self.assertRaises(ValidationError):
            self.create_data_table_group(project)
        data_table_group = self.create_data_table_group(name='Valid Test Dataset')
        with self.assertRaises(ValidationError):
            self.create_data_file(data_table_group, project)

    def test_slugs(self):
        project = self.default_project
        self.assertTrue(project.slug)
        dataset = project.data_table_groups.create(name='Test Miracle Dataset', creator=self.default_user)
        self.assertTrue(dataset.slug)


class ProjectGroupMembershipTest(BaseMiracleTest):

    def test_project_group(self):
        project = self.default_project
        group = project.group
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
            viewable_projects = Project.objects.viewable(user)
            self.assertEqual(project, viewable_projects[0])

        for user in users:
            self.assertTrue(project.has_group_member(user))
            project.remove_group_member(user)
            self.assertFalse(project.has_group_member(user))
            viewable_projects = Project.objects.viewable(user)
            self.assertFalse(viewable_projects)

        second_group = [self.create_user(username='externaltestuser' + str(i)) for i in xrange(0, 15)]
        for user in second_group:
            self.assertFalse(project.has_group_member(user))


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


class AnalysisParametersTest(BaseMiracleTest):

    def test_input_parameter_values(self):
        test_parameters = {
            'n': (AnalysisParameter.ParameterType.numeric, 17.1),
            'i': (AnalysisParameter.ParameterType.integer, 16),
            'c': (AnalysisParameter.ParameterType.character, 'Foof'),
            'b': (AnalysisParameter.ParameterType.logical, True),
        }
        analysis = self.default_analysis
        for name, v in test_parameters.items():
            analysis.parameters.create(name=name, data_type=v[0], default_value=v[1])
        d = analysis.get_deployr_parameters_dict()
        # d should only contain default values and be of the form:
        # { <parameter_name>: { 'type': 'primitive', 'rclass': <parameter_data_type>, 'value': <parameter_value> } }
        for k, v in d.items():
            # FIXME: add type coercion so AnalysisParameter values are converted to the appropriate value type?
            self.assertEqual(unicode(v['value']), unicode(test_parameters[k][1]))

        updated_test_parameters = {
            'n': 23.4,
            'i': 12,
            'c': 'Groof',
            'b': False,
        }
        d = analysis.get_deployr_parameters_dict(values=updated_test_parameters)
        for k, v in d.items():
            # FIXME: add type coercion so AnalysisParameter values are converted to the appropriate value type?
            self.assertEqual(unicode(v['value']), unicode(updated_test_parameters[k]))

