import os
from django.test.utils import override_settings

from ..ingest.analyzer import (group_files, ShapefileFileGroup, ProjectGroupedFilePaths,
                               OtherFile, extract_metadata, sanitize_ext, TabularLoader)
from ..ingest.unarchiver import ProjectFilePaths
from .common import BaseMiracleTest


class AnalyzerTest(BaseMiracleTest):
    TEST_PROJECT_DIRECTORY = os.path.join(os.getcwd(),
                                          "miracle", "core", "tests", "projects",
                                          "skeleton", "test")
    TEST_DATA_DIRECTORY = os.path.join(os.getcwd(),
                                       "miracle", "core")

    def test_sanitize_ext(self):
        ext = ".ZIP"
        self.assertEqual(sanitize_ext(ext), ".zip")

    def test_shp(self):
        test_data = self.get_test_data("cities.shp")
        data = extract_metadata(test_data)
        columns = data.layers[0][1]
        self.assertItemsEqual(columns,
                              ((u'Density', 'decimal'), (u'Name', 'text'),
                               (u'Created', 'date'), (u'Population', 'decimal')))

    def test_asc(self):
        test_data = self.get_test_data("sample.asc")
        data = extract_metadata(test_data)
        self.assertEqual(data.properties.get('width'), 4)
        self.assertEqual(data.properties.get('height'), 6)
        self.assertEqual(data.layers, [(None, (('description', u''),))])

    def test_jpg(self):
        data = extract_metadata(self.get_test_data("sample.jpg"))
        self.assertEqual(data.properties.get('width'), 192)
        self.assertEqual(data.properties.get('height'), 256)
        self.assertEqual(data.layers, [(None, (('description', u''),)),
                                       (None, (('description', u''),)),
                                       (None, (('description', u''),))])

    def test_headeredcsv(self):
        data = extract_metadata(self.get_test_data("head.csv"))
        self.assertEqual(data.layers[0], (None, (('ID', 'bigint'), ('Town', 'text'))))

    def test_headlesscsv(self):
        data = extract_metadata(self.get_test_data("headless.csv"))
        self.assertEqual(data.layers[0], (None, ((None, 'bigint'), (None, 'text'), (None, 'date'))))

    def test_netlogocsv(self):
        data = extract_metadata(self.get_test_data("netlogo.csv"))
        return True

    def test_luxecsv(self):
        data = extract_metadata(self.get_test_data("luxe.csv"))
        self.assertEqual(data.layers[0][1][0], ("agent_id", "bigint"))

    @override_settings(MIRACLE_PROJECT_DIRECTORY=TEST_PROJECT_DIRECTORY)
    def test_groups_shp(self):
        files = map(lambda x: self.get_test_data(x), ['cities.dbf', 'cities.prj', 'cities.shp', 'cities.shx'])
        project_grouped_file_paths = ProjectGroupedFilePaths(project_token="test",
                                                             grouped_paths=[ShapefileFileGroup(files, (0, 1, 2, 3))],
                                                             paths=files)
        columns = project_grouped_file_paths.grouped_paths[0].metadata.layers[0][1]
        self.assertItemsEqual(columns,
                              ((u'Density', 'decimal'), (u'Name', 'text'),
                               (u'Created', 'date'), (u'Population', 'decimal')))

    def test_guess_type(self):
        self.assertEqual(TabularLoader._guess_type(("1.0","2.0")), "decimal")
        self.assertEqual(TabularLoader._guess_type(("1","-2.0")), "decimal")
        # scientific notation is parsed as a decimal
        self.assertEqual(TabularLoader._guess_type(("1.0e10", "1.2e+10")), "decimal")
        self.assertEqual(TabularLoader._guess_type(
            ("0.8233835390990336", "0.8548997656615668", "0.839332627951762")), "decimal")


        self.assertEqual(TabularLoader._guess_type(("1","a")), "text")
        # Zero padded strings are not considered numbers
        self.assertEqual(TabularLoader._guess_type(("00", "1.0")), "text")

        self.assertEqual(TabularLoader._guess_type(("1 ", "-2")), "bigint")

        self.assertEqual(TabularLoader._guess_type((' "t"', ' false')), "boolean")
        self.assertEqual(TabularLoader._guess_type((' "t"', 'faLse')), "boolean")