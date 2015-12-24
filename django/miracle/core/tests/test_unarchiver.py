import shutil

import mock
import os
from os import path
from django.conf import settings

from ...core.ingest.unarchiver import extract, _validate_project_structure, PackratException
from .common import BaseMiracleTest


class ArchiveExtractorTest(BaseMiracleTest):
    PROJECT_TEST_DIR = "miracle/core/tests/projects"

    @staticmethod
    def make_archive(src):
        shutil.make_archive(src, "zip", root_dir=src)
        return src + ".zip"

    @staticmethod
    def cleanup(src, token):
        os.unlink(src)
        folder = path.join(settings.MIRACLE_PROJECT_DIRECTORY, token)
        if path.exists(folder):
            shutil.rmtree(folder)

    def test_archive_extractor(self):
        token = "test"
        project = self.create_project(name=token)
        src = path.join(self.PROJECT_TEST_DIR, "skeleton")
        archive = self.make_archive(src)
        try:
            project_folder = extract(project, archive)
            self.assertEqual(project.name, token)
            self.assertItemsEqual(project_folder.paths,
                                  ["README.md", "src/init.R", "data/data.csv"])
        finally:
            self.cleanup(archive, token)

    @mock.patch('miracle.core.ingest.unarchiver.path')
    def test_validate_project_structure(self, mock_path):
        mock_path.isdir.return_value = True
        _validate_project_structure("", "")

        mock_path.isdir.return_value = False
        with self.assertRaises(PackratException):
            _validate_project_structure("", "")
