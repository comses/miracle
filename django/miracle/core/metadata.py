"""
Read files and extract metadata
"""
import csv
import os
import collections
import dateutil.parser as date
from enum import Enum
from os import path
from django.conf import settings
from django.contrib.gis.gdal import DataSource, GDALRaster, GDALException

import logging

logger = logging.getLogger(__name__)

DataTypes = Enum('DataTypes', 'none archive code data document vizualization')


class ProjectMetadata(object):
    def __init__(self, name, file_metadata, log):
        self.name = name
        self.file_metadata = file_metadata
        self.log = log

    def __repr__(self):
        return "ProjectMetadata(%s, %s)" % \
               (self.file_metadata, self.log)


class Metadata(object):
    """
    Metadata for one dataset instance. Dataset instances are grouped by the user
    into Datasets later.
    """
    def __init__(self, fullpath, datatype, properties, layers, errors=[]):
        self.path = fullpath
        self.datatype = datatype
        self.properties = properties
        self.layers = layers
        self.errors = errors

    def __repr__(self):
        res = "Metadata(%s, %s, %s, %s)\n" % \
              (self.path, self.datatype, self.properties, self.layers)
        return res


class GDALLoader(object):
    @staticmethod
    def from_file(path):
        datasource = GDALRaster(path)
        properties = {"width": datasource.width,
                      "height": datasource.height}
        try:
            properties["srs"] = datasource.srs
        except GDALException:
            pass
        layers = [GDALLoader.from_layer(band) for band in datasource.bands]

        return Metadata(path, "data", properties, layers)

    @staticmethod
    def from_layer(layer):
        return {"description": layer.description}


class OGRLoader(object):
    @staticmethod
    def from_file(path):
        datasource = DataSource(path)
        properties = {}
        layers = [OGRLoader.from_layer(layer) for layer in datasource]

        return Metadata(path, DataTypes.data, properties, layers)

    OGR_DATATYPE_CONVERSIONS = {
        "OFTString": "String",
        "OFTReal": "Real",
        "OFTDate": "Date"
    }

    @staticmethod
    def from_layer(layer):
        return {field: OGRLoader.OGR_DATATYPE_CONVERSIONS[datatype.__name__]
                for (field, datatype) in zip(layer.fields, layer.field_types)}


"""
class MP4Loader(object):
    @staticmethod
    def from_file(path):
        filename, realname = unicodeFilename(path), path
        _, ext = os.path.splitext(path)
        parser = createParser(filename, realname)
        if not parser:
            raise Exception("Unable to parse file %s" % path)

        metadata = extractMetadata(parser)
        datatype = DataTypes.vizualization
        properties = {"width": metadata.getText("width"),
                      "height": metadata.getText("height"),
                      "bit_rate": metadata.getText("bit_rate")}
        layers = []

        return Metadata(path, datatype, properties, layers)
"""


class ArchiveLoader(object):
    @staticmethod
    def from_file(path):
        return Metadata(path, DataTypes.archive, {}, [])


class TabularLoader(object):
    @staticmethod
    def from_file(path):
        if TabularLoader._is_netlogo(path):
            return TabularLoader._read_netlogo_csv(path)
        else:
            return TabularLoader._read_normal_csv(path)

    @staticmethod
    def _read_netlogo_csv(path):
        with open(path, 'rb') as f:
            data = csv.reader(f)

            # extract the metadata
            next(data)  # ignore Netlogo Version
            file_name = next(data)
            model_name = next(data)
            next(data)  # ignore timestamp of last run
            next(data)  # ignore slider name ranges
            next(data)  # ignore slider ranges

            colnames = next(data)
            datasample = next(data)
            datatypes = [TabularLoader._guess_type(el) for el in datasample]

            properties = {"file_name": file_name, "model_name": model_name}
            layers = [{name: datatype for name, datatype in zip(colnames, datatypes)}]

            return Metadata(path, DataTypes.data, properties, layers)

    @staticmethod
    def _read_normal_csv(path):
        properties = {}
        with open(path, 'rb') as f:
            try:
                has_header = csv.Sniffer().has_header(f.read(8192))
            except Exception as e:
                return Metadata(path, DataTypes.data, properties, [], [e])

            f.seek(0)
            layer = {}
            if has_header:
                reader = csv.DictReader(f)
                row = reader.next()
                for k, v in row.iteritems():
                    layer[k] = TabularLoader._guess_type(v)
            else:
                reader = csv.reader(f)
                row = reader.next()
                n = len(row)
                for i in xrange(n):
                    layer["col%s" % i] = TabularLoader._guess_type(row[i])

            layers = [layer]

        return Metadata(path, DataTypes.data, properties, layers)

    @staticmethod
    def _guess_type(element):
        try:
            float(element)
            return "Real"
        except ValueError:
            pass
        try:
            date.parse(element)
            return "Date"
        except ValueError:
            pass
        return "String"

    @staticmethod
    def _is_netlogo(path):
        """
        determine if file is NetLogo or regular formatted csv
        """
        try:
            with open(path, 'rb') as f:
                reader = csv.reader(f)
                i = 0

                row_len = len(next(reader))
                while i < 6:
                    row = next(reader)
                    n = len(row)
                    if n != row_len:
                        return True

                    i += 1

            return False

        except StopIteration:
            return False


class CodeLoader(object):
    @staticmethod
    def from_file(path):
        return Metadata(path, DataTypes.code, {}, [])


class DocumentLoader(object):
    @staticmethod
    def from_file(path):
        return Metadata(path, DataTypes.document, {}, [])


class UnknownLoader(object):
    @staticmethod
    def from_file(path):
        return Metadata(path, DataTypes.none, {}, [])

CONSTRUCTOR_FORMATS = {
    ArchiveLoader.from_file: frozenset([".bzip2", ".gzip", ".zip", ".7z", ".tar"]),
    # MP4Loader.from_file: frozenset([".mp4"]),
    TabularLoader.from_file: frozenset([".csv", ".tsv"]),
    OGRLoader.from_file: frozenset([".shp"]),
    GDALLoader.from_file: frozenset([".jpg", ".gif", ".png", ".asc"]),
    CodeLoader.from_file: frozenset([".r", ".java", ".py", ".pl", ".jl", ".nlogo", ".sh"]),
    DocumentLoader.from_file: frozenset([".md", ".rmd", ".ipynb", ".rtf", ".pdf", ".doc", ".docx", ".rst", ".html", ".txt"])
}

FORMAT_DISPATCH = \
    collections.defaultdict(lambda: UnknownLoader.from_file)

for constructor, formats in CONSTRUCTOR_FORMATS.iteritems():
    for fmt in formats:
        FORMAT_DISPATCH[fmt] = constructor


def sanitize_ext(ext):
    return ext.lower()


def load_metadata(path):
    """
    Create metadata from a path based on its extension

    :param path: the path to the file/directory you want to load
    :return: metadata object of the file/directory you load
    """
    _, ext = os.path.splitext(path)
    ext = sanitize_ext(ext)
    return FORMAT_DISPATCH[ext](path)
