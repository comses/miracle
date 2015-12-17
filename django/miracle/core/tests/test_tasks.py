from os import path
import shutil
import os

from django.core.files import File
from django.conf import settings
from django.test.utils import override_settings

from .common import BaseMiracleTest
from ..models import Dataset, DataTableColumn, DataTable, DatasetFile, Project
from miracle.core.tasks import run_metadata_pipeline

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
        folder = path.join(settings.MIRACLE_PROJECT_DIRECTORY, token)
        if path.exists(folder):
            shutil.rmtree(folder)

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_metadata_pipeline(self):
        token = "test"
        project = self.create_project(name=token)
        src = path.join(self.TEST_PROJECT_DIRECTORY, "skeleton")
        archive = self.make_archive(src)
        file_archive = File(open(archive, 'r'))
        project.write_archive(file_archive)
        try:
            run_metadata_pipeline(project, project.archive_path).apply_async().get()
            self.assertEqual(len(Dataset.objects.filter(name="data")), 1)
            self.assertEqual(len(DataTableColumn.objects.all()), 2)
        finally:
            self.cleanup(project)