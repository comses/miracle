"""
Read files and extract metadata
"""
import csv
import os
from django.contrib.gis.gdal import DataSource, GDALRaster, GDALException

from hachoir_core.cmd_line import unicodeFilename
from hachoir_parser import createParser
from hachoir_metadata import extractMetadata

HACHOIR_FORMATS = frozenset([".bzip2", ".gzip", ".zip", ".tar", ".mp4"])
TABULAR_FORMATS = frozenset([".csv", ".tsv"])
OGR_FORMATS = frozenset([".shp"])
GDAL_FORMATS = frozenset([".jpg", ".gif", ".png", ".asc"])
R_FORMAT = frozenset([".r"]) # use rpy2 and c(lsl.str()) to function names

class MetadataFileExtNotFoundError(Exception): pass

class Metadata(object):
    def __init__(self, path):
        self.path = path
        fname, fext = os.path.splitext(path)

        if fext in OGR_FORMATS:
            self._fromOGR(path)
        elif fext in GDAL_FORMATS:
            self._fromGDAL(path)
        elif fext in HACHOIR_FORMATS:
            self._fromHachoir(path, fext)
        elif fext in TABULAR_FORMATS:
            self._fromTabular(path)
        elif fext in R_FORMAT:
            self._fromR(path)
        else:
            raise MetadataFileExtNotFoundError("file extension %s not supported" % fext)

    def _fromOGR(self, path):
        datasource = DataSource(path)
        self.properties = {}
        self.layers = [fromOGRLayer(layer) for layer in datasource]

    def _fromGDAL(self, path):
        datasource = GDALRaster(path)
        self.properties = {"width": datasource.width,
                           "height": datasource.height}
        try:
            self.properties["srs"] = datasource.srs
        except GDALException: pass
        self.layers = [fromGDALLayer(band) for band in datasource.bands]

    def _fromHachoir(self, path, fext):
        filename, realname = unicodeFilename(path), path
        parser = createParser(filename, realname)
        if not parser:
            raise Exception("Unable to parse file %s" % path)

        metadata = extractMetadata(parser)
        if fext in {".mp4"}:
            self.properties = {"width": metadata.getText("width"),
                               "height": metadata.getText("height"),
                               "bit_rate": metadata.getText("bit_rate")}
        elif fext in {".bzip2", ".gzip", ".tar", ".zip"}:
            # TODO
            self.properties = {}
        else:
            self.properties = {}
        self.layers = []

    def _fromTabular(self, path):
        def addProperty(layer, name, value):
            if type(value) is str:
                layer[name] = "OFTString"
            elif type(value) is float:
                layer[name] = "OFTReal"
            else:
                raise Exception("Unsupported type (%s, %s)" % (name, type(value)))

        self.properties = {}
        with open(path, 'rb') as f:
            has_header = csv.Sniffer().has_header(f.read(8192))

            f.seek(0)
            layer = {}
            if has_header:
                reader = csv.DictReader(f)
                row = reader.next()
                for  k, v in row.iteritems():
                    addProperty(layer, k, v)
            else:
                reader = csv.reader(f)
                row = reader.next()
                n = len(row)
                for i in xrange(n):
                    addProperty(layer, "col%s" % i, row[i])

            self.layers = [layer]

    def _fromR(self, path): pass

    def __str__(self):
        res = "Metadata(%s, %s, %s)" % (self.path, self.properties, self.layers)
        return res

def fromOGRLayer(layer):
    return {key: val.__name__ for (key, val) in zip(layer.fields, layer.field_types)}

def fromGDALLayer(layer):
    return {"description": layer.description}