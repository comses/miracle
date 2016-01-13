import mock

from .common import BaseMiracleTest, logger
from ..models import Project
from django.core.urlresolvers import reverse

import json


class ProjectListTest(BaseMiracleTest):

    fixtures = ['test-projects.json']

    def _get_project_list(self):
        return self.get('core:project-list', {'format': 'json'})

    def test_project_list_access(self):
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
        # all projects should now be accessible since they are published
        self.assertEqual(len(projects), 16)
        for project in Project.objects.all():
            project.unpublish(self.default_user)
        response = self._get_project_list()
        # back to inaccessible
        self.assertFalse(json.loads(response.content))

    @mock.patch('miracle.core.views.AsyncResult')
    def test_task_status_loads(self, async_result):
        async_result_mock = mock.Mock()
        async_result_mock.status = "SUCCESS"
        async_result_mock.ready.return_value = True
        async_result.return_value = async_result_mock
        self.login()
        url = reverse('core:upload-status',kwargs={'task_uuid':'a3fb4f-4f43f'})
        response = self.get(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, "SUCCESS")
