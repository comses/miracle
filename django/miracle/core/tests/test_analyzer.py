import os
from django.test.utils import override_settings

from ..ingest.analyzer import (group_files, ShapefileFileGroup, ProjectGroupedFilePaths,
                               OtherFile, extract_metadata, sanitize_ext)
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
                              ((u'Density', 'Real'), (u'Name', 'String'),
                               (u'Created', 'Date'), (u'Population', 'Real')))

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
        self.assertEqual(data.layers[0], (None, (('ID', 'Real'), ('Town', 'String'))))

    def test_headlesscsv(self):
        data = extract_metadata(self.get_test_data("headless.csv"))
        self.assertEqual(data.layers[0], (None, ((None, 'Real'), (None, 'String'), (None, 'Date'))))

    def test_netlogocsv(self):
        data = extract_metadata(self.get_test_data("netlogo.csv"))
        return True

    def test_luxecsv(self):
        data = extract_metadata(self.get_test_data("luxe.csv"))
        self.assertEqual(data.layers[0][1][0], ("agent_id", "Real"))

    @override_settings(MIRACLE_PROJECT_DIRECTORY=TEST_PROJECT_DIRECTORY)
    def test_groups_shp(self):
        files = map(lambda x: self.get_test_data(x), ['cities.dbf', 'cities.prj', 'cities.shp', 'cities.shx'])
        project_grouped_file_paths = ProjectGroupedFilePaths(project_token="test",
                                                             grouped_paths=[ShapefileFileGroup(files, (0, 1, 2, 3))],
                                                             paths=files)
        columns = project_grouped_file_paths.grouped_paths[0].metadata.layers[0][1]
        self.assertItemsEqual(columns,
                              ((u'Density', 'Real'), (u'Name', 'String'),
                               (u'Created', 'Date'), (u'Population', 'Real')))
