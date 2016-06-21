from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory, Client
from django.utils.http import urlencode

from miracle.core.models import (DataAnalysisScript, Project, DataColumn, DataTableGroup, DataFile)

import logging
import os

logger = logging.getLogger(__name__)


class BaseMiracleTest(TestCase):

    """
    Base class providing common scaffolding for miracle tests
    """

    TEST_DATA_DIR = os.path.join(settings.BASE_DIR, 'miracle', 'core', 'tests', 'data')

    def setUp(self, **kwargs):
        self.client = Client()
        self.factory = RequestFactory()
        self.logger = logger
        self.default_user = self.create_user()
        self.default_project = self.create_project()
        self.default_script_file = os.path.join(self.TEST_DATA_DIR, 'example.R')
        self.default_analysis = self.create_analysis(creator=self.default_user)

    @property
    def default_project_name(self):
        return "{} Project".format(type(self).__name__)

    @property
    def default_analysis_name(self):
        return "test_analysis.zip"

    @property
    def default_analysisscript_params(self):
        return [{"name": "sdp2",
                 "label": "Standard deviation of preference to proximity",
                 "render": "numeric",
                 "default": 0.4,
                 "valueList": [0, 0.1, 0.2, 0.3, 0.4, 0.5]},
                {"name": "sdb3",
                 "label": "Standard deviation of budget",
                 "render": "integer",
                 "default": 30,
                 "valueRange": [0, 50, 10]}]

    @property
    def login_url(self):
        return reverse('login')

    @property
    def profile_url(self):
        return reverse('core:profile')

    @property
    def dashboard_url(self):
        return reverse('core:dashboard')

    def get_test_data(self, filename):
        return os.path.join(self.TEST_DATA_DIR, filename)

    def create_user(self, username='testuser', email='miracle-test@mailinator.com',
                    first_name='Default', last_name='Testuser', password='test'):
        return User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )

    def create_analysis(self, name=None, project=None, creator=None, script_file=None, parameters=None):
        if name is None:
            name = self.default_analysis_name
        if project is None:
            project = self.default_project
        if creator is None:
            creator = self.default_user
        if script_file is None:
            script_file = self.default_script_file
        if parameters is None:
            parameters = self.default_analysisscript_params
        analysis = DataAnalysisScript.objects.create(creator=creator,
                                                     name=name,
                                                     project=project,
                                                     archived_file=script_file)
        analysis.add_parameters(parameters)
        return analysis

    def create_project(self, name=None, user=None):
        if name is None:
            name = self.default_project_name
        if user is None:
            user = self.default_user
        project = Project(name=name, creator=user)
        project.full_clean()
        project.save()
        return project

    def create_data_table_group(self, project=None, name=None, creator=None):
        if project is None:
            project = self.default_project
        if creator is None:
            creator = project.creator
        data_table_group = DataTableGroup(project=project, name=name, creator=creator)
        data_table_group.full_clean()
        data_table_group.save()
        return data_table_group

    def create_data_file(self, data_table_group=None, project=None):
        if project is None:
            if data_table_group is None:
                self.fail("DataFile requires parent data table group or project")
            else:
                project = data_table_group.project
        df = DataFile(data_table_group=data_table_group, project=project)
        df.full_clean()
        df.save()
        return df

    def create_column(self, data_table_group=None, name=None):
        if data_table_group is None:
            self.fail("column requires parent data_table_group")
        column = DataColumn(data_table_group=data_table_group, name=name)
        column.full_clean()
        column.save()
        return column

    def reverse(self, viewname, query_parameters=None, **kwargs):
        reversed_url = reverse(viewname, **kwargs)
        if query_parameters is not None:
            return '%s?%s' % (reversed_url, urlencode(query_parameters))
        return reversed_url

    def login(self, username=None, password=None, user=None):
        if username is None or password is None:
            if user is None:
                user = self.default_user
            username = user.username
            password = 'test'
        return self.client.login(username=username, password=password)

    def logout(self):
        return self.client.logout()

    def post(self, url, *args, **kwargs):
        if ':' in url:
            url = self.reverse(url)
        return self.client.post(url, *args, **kwargs)

    def get(self, url, *args, **kwargs):
        if ':' in url:
            url = self.reverse(url)
        return self.client.get(url, *args, **kwargs)

    class Meta:
        abstract = True
