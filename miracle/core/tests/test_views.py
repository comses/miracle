from .common import BaseMiracleTest, logger
from ..models import Project

import json


class ProjectListTest(BaseMiracleTest):

    fixtures = ['test-projects.json']

    def _get_project_list(self):
        response = self.get('core:project_list', {'format': 'json'})
        projects = json.loads(response.content)
        project_list = json.loads(projects['project_list_json'])
        return project_list

    def test_project_list_view(self):
        projects = self._get_project_list()
        # none of the initial projects have been published, should have no projects available to unauthenticated user
        self.assertFalse(projects)
        for p in Project.objects.all():
            p.add_group_member(self.default_user)
        self.login()
        self.assertEqual(len(self._get_project_list()), 16)
        self.logout()
        self.assertEqual(len(self._get_project_list()), 0)
        for project in Project.objects.all():
            project.publish(self.default_user)
        self.assertEqual(len(self._get_project_list()), 16)
