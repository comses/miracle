from .common import BaseMiracleTest, logger
from ..metadata import load_metadata, sanitize_ext


class MetadataTest(BaseMiracleTest):
    def test_sanitize_ext(self):
        ext = ".ZIP"
        self.assertEqual(sanitize_ext(ext), ".zip")

    def test_shp(self):
        data = load_metadata(self.get_test_data("cities.shp"))
        self.assertEqual(data.layers,
                         [{u'Density': 'Real', u'Name': 'String',
                           u'Created': 'Date', u'Population': 'Real'}])

    def test_asc(self):
        data = load_metadata(self.get_test_data("sample.asc"))
        self.assertEqual(data.properties, {'width': 4, 'height': 6})
        self.assertEqual(data.layers, [{'description': u''}])

    def test_jpg(self):
        data = load_metadata(self.get_test_data("sample.jpg"))
        self.assertEqual(data.properties, {'width': 192, 'height': 256})
        self.assertEqual(data.layers, [{'description': u''}, {'description': u''}, {'description': u''}])

    def test_mp4(self):
        data = load_metadata(self.get_test_data("small.mp4"))
        self.assertEqual(data.properties, {'width': u'560 pixels', 'bit_rate': None, 'height': u'320 pixels'})
        self.assertFalse(data.layers)

    def test_headeredcsv(self):
        data = load_metadata(self.get_test_data("head.csv"))
        self.assertEqual(data.layers, [{'Town': 'String', 'ID': 'Real'}])

    def test_headlesscsv(self):
        data = load_metadata(self.get_test_data("headless.csv"))
        self.assertEqual(data.layers, [{'col0': 'Real', 'col1': 'String', 'col2': 'Date'}])

    def test_netlogocsv(self):
        data = load_metadata(self.get_test_data("netlogo.csv"))
        return True
