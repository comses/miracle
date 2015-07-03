from .common import BaseMiracleTest, logger
from ..models import Project

import json


class ProjectListTest(BaseMiracleTest):

    fixtures = ['test-projects.json']

    def _get_project_list(self):
        return self.get('core:project-list', {'format': 'json'})

    def test_project_list_view(self):
        response = self._get_project_list()
        # none of the initial projects have been published, should have no projects available to unauthenticated user
        self.assertFalse(json.loads(response.content))
        for p in Project.objects.all():
            p.add_group_member(self.default_user)
        self.login()
        response = self._get_project_list()
        projects = json.loads(response.content)
        self.assertEqual(len(projects), 16)
        self.logout()
        response = self._get_project_list()
        self.assertFalse(json.loads(response.content))
        for project in Project.objects.all():
            project.publish(self.default_user)
        response = self._get_project_list()
        projects = json.loads(response.content)
        self.assertEqual(len(projects), 16)
        for project in Project.objects.all():
            project.unpublish(self.default_user)
        response = self._get_project_list()
        self.assertFalse(json.loads(response.content))

