import os, shutil
from django.conf import settings

from .common import BaseMiracleTest
from ..extractors import Extractor
from ...settings import MIRACLE_ANALYSIS_DIRECTORY

class ExtractorsTest(BaseMiracleTest):
    ANALYSIS_PATH = os.path.join(settings.BASE_DIR, 'miracle', 'core', 'tests', 'analyses')

    def setUp(self):
        rel_file_paths = os.listdir(MIRACLE_ANALYSIS_DIRECTORY)
        for rel_file_path in rel_file_paths:
            file_path = os.path.join(MIRACLE_ANALYSIS_DIRECTORY, rel_file_path)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    def test_bad_shp(self):
        """
        extracting metadata from a shapefile not meeting the specification logs an error
        """
        extract = Extractor.from_archive(os.path.join(self.ANALYSIS_PATH, "bad_shp_test.zip"), "1")
        analysis_metadata = extract.extract_metadata()
        self.assertTrue(analysis_metadata.log[0].startswith("Shapefile is missing extensions"))

    def test_unsupported_archive_format(self):
        """
        unsupported archive formats should throw an error
        """
        with self.assertRaises(ValueError):
            Extractor.from_archive(os.path.join(self.ANALYSIS_PATH, "unsupported.txt"), "2")

    def test_r_example(self):
        extract = Extractor.from_archive(os.path.join(self.ANALYSIS_PATH, "r_example.7z"), "3")
        analysis_metadata = extract.extract_metadata()
        with open(os.path.join(self.ANALYSIS_PATH, "test.txt"), mode="a") as f:
            f.write(analysis_metadata.__str__())
        self.assertTrue(True)

    def test_luxe(self):
        extract = Extractor.from_archive(os.path.join(self.ANALYSIS_PATH, "luxe.7z"), "4")
        analysis_metadata = extract.extract_metadata()
        with open(os.path.join(self.ANALYSIS_PATH, "test.txt"), mode="a") as f:
            f.write(analysis_metadata.__str__())
        self.assertTrue(True)

    def test_shp(self):
        extract = Extractor.from_archive(os.path.join(self.ANALYSIS_PATH, "shp_test.zip"), "5")
        analysis_metadata = extract.extract_metadata()
        with open(os.path.join(self.ANALYSIS_PATH, "test.txt"), mode="a") as f:
            f.write(analysis_metadata.__str__())
        self.assertTrue(True)

    def test_lithic_assemblages(self):
        extract = Extractor.from_archive(os.path.join(self.ANALYSIS_PATH, "lithic_assemblages.zip"), "6")
        analysis_metadata = extract.extract_metadata()
        with open(os.path.join(self.ANALYSIS_PATH, "test.txt"), mode="a") as f:
            f.write(analysis_metadata.__str__())
        self.assertTrue(True)