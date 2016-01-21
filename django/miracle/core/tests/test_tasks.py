from os import path
import shutil
import os
import mock
import requests

from django.core.files import File
from django.conf import settings
from django.test.utils import override_settings

from .common import BaseMiracleTest
from ..models import DataTableGroup, DataColumn, DataFile, Project
from miracle.core.tasks import run_metadata_pipeline
from ..ingest import PackratException


class TaskTests(BaseMiracleTest):
    TEST_PROJECT_DIRECTORY = "miracle/core/tests/projects"

    @staticmethod
    def make_archive(src):
        shutil.make_archive(src, "zip", root_dir=src)
        return src + ".zip"

    @staticmethod
    def cleanup(project):
        token = project.name
        src = project.archive_path
        os.unlink(src)
        project_folder = path.join(settings.MIRACLE_PROJECT_DIRECTORY, token)
        packrat_folder = path.join(settings.MIRACLE_PACKRAT_DIRECTORY, token)
        if path.exists(project_folder):
            shutil.rmtree(project_folder)
        if path.exists(packrat_folder):
            shutil.rmtree(packrat_folder)

    @mock.patch('miracle.core.ingest.loader.login')
    @mock.patch('miracle.core.ingest.loader.DeployrAPI.upload_script')
    @mock.patch('miracle.core.ingest.loader.DeployrAPI.create_working_directory')
    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_metadata_pipeline_success(self, cwd, upload_script, login):
        post_result_mock = mock.Mock()
        post_result_mock.status_code = 200
        cwd.return_value = post_result_mock
        upload_script.return_value = post_result_mock

        login_result_mock = mock.MagicMock(spec=requests.Session)
        login.return_value = login_result_mock

        token = "test"
        project = self.create_project(name=token)
        src = path.join(self.TEST_PROJECT_DIRECTORY, "skeleton")
        archive = self.make_archive(src)
        file_archive = File(open(archive, 'r'))
        project.write_archive(file_archive)

        try:
            run_metadata_pipeline.delay(project, project.archive_path)
            self.assertEqual(len(DataTableGroup.objects.filter(name="data")), 1)
            self.assertEqual(len(DataColumn.objects.all()), 2)
        finally:
            self.cleanup(project)
