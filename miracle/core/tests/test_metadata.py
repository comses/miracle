from .common import BaseMiracleTest, logger
from ..metadata import Metadata, MetadataFileExtNotFoundError
import os


class MetadataTest(BaseMiracleTest):

    def test_shp(self):
        data = Metadata(self.get_test_data("cities.shp"))
        self.assertEqual(data.layers,
                         [{u'Density': 'OFTReal', u'Name': 'OFTString',
                           u'Created': 'OFTDate', u'Population': 'OFTReal'}])

    def test_asc(self):
        data = Metadata(self.get_test_data("sample.asc"))
        self.assertEqual(data.properties, {'width': 4, 'height': 6})
        self.assertEqual(data.layers, [{'description': u''}])

    def test_jpg(self):
        data = Metadata(self.get_test_data("sample.jpg"))
        self.assertEqual(data.properties, {'width': 192, 'height': 256})
        self.assertEqual(data.layers, [{'description': u''}, {'description': u''}, {'description': u''}])

    def test_mp4(self):
        data = Metadata(self.get_test_data("small.mp4"))
        self.assertEqual(data.properties, {'width': u'560 pixels', 'bit_rate': None, 'height': u'320 pixels'})
        self.assertFalse(data.layers)

    def test_headeredcsv(self):
        data = Metadata(self.get_test_data("head.csv"))
        self.assertEqual(data.layers, [{'Town': 'OFTString', 'ID': 'OFTString'}])

    def test_headlesscsv(self):
        data = Metadata(self.get_test_data("headless.csv"))
        self.assertEqual(data.layers, [{'col0': 'OFTString', 'col1': 'OFTString'}])

    def test_unsupported_file_format(self):
        with self.assertRaises(MetadataFileExtNotFoundError):
            Metadata("blah.abc")
