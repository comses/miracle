from ..metadata import Metadata, MetadataFileExtNotFoundError
import pytest

def test_shp():
    data = Metadata("data/cities.shp")
    assert data.layers == \
        [{u'Density': 'OFTReal', u'Name': 'OFTString', u'Created': 'OFTDate', u'Population': 'OFTReal'}]

def test_asc():
    data = Metadata("data/sample.asc")
    assert data.properties == \
           {'width': 4, 'height': 6}
    assert data.layers == [{'description': u''}]

def test_jpg():
    data = Metadata("data/sample.jpg")
    assert data.properties == \
        {'width': 192, 'height': 256}
    assert data.layers == [{'description': u''},{'description': u''},{'description': u''}]

def test_mp4():
    data = Metadata("data/small.mp4")
    assert data.properties == \
        {'width': u'560 pixels', 'bit_rate': None, 'height': u'320 pixels'}
    assert data.layers == []

def test_headeredcsv():
    data = Metadata("data/head.csv")
    assert data.layers == [{'Town': 'OFTString', 'ID': 'OFTString'}]

def test_headlesscsv():
    data = Metadata("data/headless.csv")
    assert data.layers == [{'col0': 'OFTString', 'col1': 'OFTString'}]

def test_unsupported_file_format():
    with pytest.raises(MetadataFileExtNotFoundError):
        Metadata("blah.abc")
