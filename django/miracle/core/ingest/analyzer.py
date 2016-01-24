import csv
import collections
import dateutil.parser as date
import json
import logging
import re

import abc

from collections import defaultdict
from django.conf import settings
from django.contrib.gis.gdal import DataSource, GDALRaster, GDALException
from os import path
import os

from ..utils import Chdir
from . import ProjectGroupedFilePaths, DataTypes

logger = logging.getLogger(__name__)

"""
Partitions files into groups for the metadata extractor
Only current grouped filetype are shapefiles
"""

class FileGroup(object):
    """
    Interface for FileGroups
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _analyze(self):
        pass

    @abc.abstractproperty
    def dispatch(self):
        pass

    @abc.abstractproperty
    def group_name(self):
        pass

    @abc.abstractproperty
    def inds(self):
        pass

    @abc.abstractproperty
    def metadata(self):
        pass

    @abc.abstractproperty
    def title(self):
        pass


class ShapefileValidationError(Exception):
    pass


class ShapefileFileGroup(FileGroup):
    def __init__(self, file_paths, inds, metadata=None):
        self._file_paths = file_paths
        self._inds = inds
        self._metadata = metadata or self._analyze()

    def __eq__(self, other):
        return isinstance(other, ShapefileFileGroup) and \
               self._file_paths == other._file_paths and \
               self._inds == other._inds

    def _analyze(self):
        metadata = OGRLoader.from_file(self.group_name)
        return metadata

    @property
    def dispatch(self):
        return ".shp"

    @property
    def group_name(self):
        for file_path in self._file_paths:
            _, ext = path.splitext(file_path)
            if ext == ".shp":
                return file_path
        raise ShapefileValidationError("no '.shp' file in {}".format(self._file_paths.__str__()))

    @property
    def inds(self):
        return self._inds

    @property
    def metadata(self):
        return self._metadata

    @property
    def title(self):
        bname, ext = path.splitext(path.basename(self.group_name))
        return bname


class ShapefileGrouper(object):
    def __init__(self):
        self._groups = defaultdict(lambda: [])

    def add(self, file_path, ind):
        file_name, ext = path.splitext(file_path)
        is_part_of_shapefile = ext in ['.shp', '.dbf', '.prj', '.shx']
        if is_part_of_shapefile:
            self._groups[file_name].append((ind, ext))
            return True
        return False

    def groups(self):
        """
        Partitions candidate shapefile _groups into valid and invalid

        Invalid shapefile _groups are assigned the unknown type
        """
        file_paths = []
        for (file_name, ind_exts) in self._groups.iteritems():
            inds, exts = zip(*ind_exts)
            if ('.dbf' not in exts) or ('.shp' not in exts):
                i = 0
                for ext in exts:
                    file_paths.append(OtherFile(file_name + ext, inds[i]))
                    i += 1
            else:
                file_paths.append(ShapefileFileGroup([file_name + ext for ext in exts], inds))
        return file_paths


class OtherFile(FileGroup):
    def __init__(self, file_path, ind, metadata=None):
        self._file_path = file_path
        self._ind = ind
        self._metadata = metadata or self._analyze()

    def __eq__(self, other):
        return isinstance(other, OtherFile) and \
               self._file_path == other._file_path and \
               self._ind == other._ind

    def _analyze(self):
        metadata = FORMAT_DISPATCH[self.dispatch](self.group_name)
        return metadata

    @property
    def dispatch(self):
        _, ext = path.splitext(self._file_path)
        return ext.lower()

    @property
    def group_name(self):
        return self._file_path

    @property
    def inds(self):
        return [self._ind]

    @property
    def metadata(self):
        return self._metadata

    @property
    def title(self):
        bname, ext = path.splitext(path.basename(self.group_name))
        return bname


class OtherFileGrouper(object):
    def __init__(self):
        self._groups = []

    def add(self, file_path, ind):
        self._groups.append(OtherFile(file_path, ind))
        return True

    def groups(self):
        return self._groups


def group_files(project_file_paths):
    """
    :param project_file_paths:
    :type project_file_paths: ProjectFilePaths
    :return:
    :rtype: ProjectGroupedFilePaths
    """
    shapefile_grouper = ShapefileGrouper()
    otherfile = OtherFileGrouper()

    with Chdir(os.path.join(settings.MIRACLE_PROJECT_DIRECTORY, project_file_paths.project_token)):
        i = 0
        for file_path in project_file_paths.paths:
            shapefile_grouper.add(file_path, i) or otherfile.add(file_path, i)
            i += 1

        file_groups = shapefile_grouper.groups() + otherfile.groups()
    return ProjectGroupedFilePaths(project_file_paths.project_token,
                                   file_groups,
                                   project_file_paths.paths)


class Metadata(object):
    """
    :type grouped_file_path: GroupedFilePath
    :type properties: dict
    :type layers: list
    """

    def __init__(self, fullpath, datatype, properties, layers, errors=None):
        self.path = fullpath
        self.datatype = datatype
        self.properties = properties
        self.layers = layers
        if not errors:
            self.errors = []
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
        layers = [(band.description or None, GDALLoader.from_layer(band)) for band in datasource.bands]

        return Metadata(path, "data", properties, layers)

    @staticmethod
    def from_layer(layer):
        return (("description", layer.description),)


class OGRLoader(object):
    @staticmethod
    def from_file(path):
        datasource = DataSource(path)
        properties = {}
        layers = [(layer.name or None, OGRLoader.from_layer(layer)) for layer in datasource]

        return Metadata(path, DataTypes.data, properties, layers)

    OGR_DATATYPE_CONVERSIONS = {
        "OFTString": "text",
        "OFTReal": "decimal",
        "OFTDate": "date"
    }

    @staticmethod
    def from_layer(layer):
        return tuple((field, OGRLoader.OGR_DATATYPE_CONVERSIONS[datatype.__name__])
                     for (field, datatype) in zip(layer.fields, layer.field_types))


class ArchiveLoader(object):
    @staticmethod
    def from_file(path):
        return Metadata(path, DataTypes.archive, {}, [])


class TabularLoader(object):
    @staticmethod
    def from_file(path):
        with open(path, "rb") as f:
            if TabularLoader._is_netlogo(f):
                f.seek(0)
                return TabularLoader._read_netlogo_csv(path, f)
            else:
                f.seek(0)
                return TabularLoader._read_normal_csv(path, f)

    ROW_SAMPLE_SIZE = 3

    @classmethod
    def _read_netlogo_csv(cls, path, f):
        data = csv.reader(f)

        # extract the metadata
        next(data)  # ignore Netlogo Version
        file_name = next(data)
        model_name = next(data)
        next(data)  # ignore timestamp of last run
        next(data)  # ignore slider name ranges
        next(data)  # ignore slider ranges

        colnames = next(data)
        datasample = cls._take_up_to_n_rows(data, cls.ROW_SAMPLE_SIZE)
        datatypes = [TabularLoader._guess_type(el) for el in datasample]

        properties = {"file_name": file_name, "model_name": model_name}
        layers = [(None, tuple((name, datatype) for name, datatype in zip(colnames, datatypes)))]

        return Metadata(path, DataTypes.data, properties, layers)

    @classmethod
    def _read_normal_csv(cls, path, f):
        properties = {}
        try:
            has_header = csv.Sniffer().has_header(f.read(4096))
        except Exception as e:
            return Metadata(path, DataTypes.data, properties, [], [e])

        f.seek(0)
        layer = []
        reader = csv.reader(f)
        if has_header:
            row = reader.next()
            row = [re.sub(r'^ *"?|"? *$', '', el) for el in row]
            row_types = cls._take_up_to_n_rows(reader, cls.ROW_SAMPLE_SIZE)
            for k, v in zip(row, row_types):
                layer.append((k, TabularLoader._guess_type(v)))
        else:
            row_types = cls._take_up_to_n_rows(reader, cls.ROW_SAMPLE_SIZE)
            n = len(row_types)
            for col in xrange(n):
                layer.append((None, TabularLoader._guess_type(row_types[col])))

        layers = [(None, tuple(layer))]

        return Metadata(path, DataTypes.data, properties, layers)

    PATTERN_BIGINT = re.compile(r'^\d+$')
    PATTERN_DECIMAL = re.compile(r'^\d+(\.\d*)*$')
    PATTERN_BOOLEAN = re.compile(r'^(true|false|t|f|yes|no)$',re.IGNORECASE)

    @classmethod
    def _guess_type(cls, elements):
        # strip leading and trailing spaces and double quotes
        elements = [re.sub(r'^ *"?|"? *$', '', el) for el in elements]
        datatype = cls._try_type(cls.PATTERN_BIGINT, elements, "bigint") or\
                   cls._try_type(cls.PATTERN_DECIMAL, elements, "decimal") or\
                   cls._try_type(cls.PATTERN_BOOLEAN, elements, "boolean")
        if datatype:
            return datatype

        try:
            for el in elements:
                date.parse(el)
            return "date"
        except ValueError:
            pass
        return "text"

    @staticmethod
    def _try_type(pattern, values, datatype):
        for value in values:
            if not re.match(pattern, value):
                return ""
        return datatype

    @staticmethod
    def _take_up_to_n_rows(reader, n):
        rows = []
        i = 0
        for row in reader:
            rows.append(row)
            i += 1
            if i >= n:
                break
        cols = zip(*rows)
        return cols

    @staticmethod
    def _is_netlogo(f):
        """
        determine if file is NetLogo or regular formatted csv
        """

        has_netlogo_in_first_row = False
        has_netlogo_in_second_row = False
        has_ragged_columns = False

        try:
            reader = csv.reader(f)
            i = 0

            row_len = 1
            row = next(reader)

            if len(row) == 1:
                has_netlogo_in_first_row = row[0].find("(NetLogo") > 0

            row = next(reader)
            if len(row) == 1:
                has_netlogo_in_second_row = row[0].find(".nlogo") > 0

            while i < 5:
                row = next(reader)
                n = len(row)
                if n != row_len:
                    has_ragged_columns = True
                    break

                i += 1

        except StopIteration:
            pass

        finally:
            return has_netlogo_in_first_row and \
                   has_netlogo_in_second_row and \
                   has_ragged_columns


class RLoader(object):
    @staticmethod
    def from_file(path):
        contents = open(path, "rb").read()
        inputs = RLoader._get_input_params(contents)
        return Metadata(path, DataTypes.code, {}, inputs)

    @staticmethod
    def _process_matches(regex, contents):
        matches = re.findall(regex, contents, flags=re.MULTILINE)
        for i in xrange(len(matches)):
            matches[i] = matches[i][2:-2]
        return matches

    @classmethod
    def _get_input_params(cls, contents):
        """
        Extracts input parameters from file contents

        Since a regular expression is being used there is the potential
        for false positives (the expression could be part of a multiline string)
        and false negatives (if the function call is being shadowed)

        Since this is an uncommon expression it should not be a problem
        """
        matches = cls._process_matches(
            "^deployrUtils::deployrInput([\S\t ]+)",
            contents)
        input_params = [json.loads(match) for match in matches]
        return [input_param for input_param in input_params
                if cls._is_valid_input_param(input_param)]

    @staticmethod
    def _is_valid_input_param(input_param):
        """
        :type input_param: dict
        """
        return input_param.has_key("name") and \
               input_param.has_key("label") and \
               input_param.has_key("render") and \
               input_param.has_key("default")


    @classmethod
    def _get_dependencies(cls, contents):
        """
        Extracts package dependencies
        """
        matches = cls._process_matches("^deployrUtils::deployrPackage([\S ]+)",
                                       contents)
        return [json.loads(match) for match in matches]


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
    RLoader.from_file: frozenset([".r"]),
    CodeLoader.from_file: frozenset([".java", ".py", ".pl", ".jl", ".nlogo", ".sh"]),
    DocumentLoader.from_file: frozenset(
        [".md", ".rmd", ".ipynb", ".rtf", ".pdf", ".doc", ".docx", ".rst", ".html", ".txt"])
}

FORMAT_DISPATCH = \
    collections.defaultdict(lambda: UnknownLoader.from_file)

for constructor, formats in CONSTRUCTOR_FORMATS.iteritems():
    for fmt in formats:
        FORMAT_DISPATCH[fmt] = constructor


def sanitize_ext(ext):
    return ext.lower()


def extract_metadata(path, constructor=None):
    """
    Create metadata from a path based on its extension

    :param path: the path to the file/directory you want to load
    :param constructor: the metadata extractor to use
    :return: metadata object of the file/directory you load
    """

    if constructor:
        return constructor(path)

    _, ext = os.path.splitext(path)
    ext = sanitize_ext(ext)
    return FORMAT_DISPATCH[ext](path)
