import shutil
import os
from os import path
from ..metadata_interface import add_project, associate_metadata_with_file
from .common import BaseMiracleTest
from ..models import DatasetFile
from django.conf import settings

class MetadataInterfaceTest(BaseMiracleTest):
    PROJECT_TEST_DIR = "miracle/core/tests/projects"

    @staticmethod
    def make_archive(src):
        shutil.make_archive(src, "zip", root_dir=src)
        return src + ".zip"

    @staticmethod
    def cleanup(src, token):
        os.unlink(src)
        shutil.rmtree(path.join(settings.MIRACLE_PROJECT_DIRECTORY, token))

    def test_packrat_extraction(self):
        token = "test"
        project = self.create_project(name=token)
        src = path.join(self.PROJECT_TEST_DIR, "skeleton")
        archive = self.make_archive(src)
        try:
            packrat = add_project(project, archive)
            self.assertEqual(project.path, token)
            self.assertItemsEqual([projectpath.filepath for projectpath in packrat.paths],
                                  ["README.md", "src/init.R", "data/data.csv"])
            analysis_projectpath = DatasetFile.objects.filter(archived_file="src/init.R").first()
            analysis = associate_metadata_with_file(analysis_projectpath)

            dataset_projectpath = DatasetFile.objects.filter(archived_file="data/data.csv").first()
            dataset = associate_metadata_with_file(dataset_projectpath)
        finally:
            self.cleanup(archive, token)
