import csv
import collections
import dateutil.parser as date
import logging

from collections import defaultdict
from django.conf import settings
from django.contrib.gis.gdal import DataSource, GDALRaster, GDALException
from fabric.api import cd
from os import path

from . import ProjectGroupedFilePaths, DataTypes, MetadataCollection, MetadataFileGroup

logger = logging.getLogger(__name__)


"""
Partitions files into groups for the metadata extractor
Only current grouped filetype are shapefiles
"""


class ShapefileValidationError(Exception):
    pass


class ShapefileFileGroup(object):

    def __init__(self, file_paths, inds):
        self._file_paths = file_paths
        self._inds = inds

    def __eq__(self, other):
        return isinstance(other, ShapefileFileGroup) and \
               self._file_paths == other._file_paths and \
               self._inds == other._inds

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

    @property
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


class OtherFile(object):

    def __init__(self, file_path, ind):
        self._file_path = file_path
        self._ind = ind

    def __eq__(self, other):
        return isinstance(other, OtherFile) and \
               self._file_path == other._file_path and \
               self._ind == other._ind

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
    def title(self):
        bname, ext = path.splitext(path.basename(self.group_name))
        return bname


class OtherFileGrouper(object):

    def __init__(self):
        self._groups = []

    def add(self, file_path, ind):
        self._groups.append(OtherFile(file_path, ind))
        return True

    @property
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

    i = 0
    for file_path in project_file_paths.paths:
        shapefile_grouper.add(file_path, i) or otherfile.add(file_path, i)
        i += 1

    return ProjectGroupedFilePaths(project_file_paths.project_token,
                                   shapefile_grouper.groups + otherfile.groups,
                                   project_file_paths.paths)


class ProjectMetadata(object):
    def __init__(self, name, file_metadata, log):
        self.name = name
        self.file_metadata = file_metadata
        self.log = log

    def __repr__(self):
        return "ProjectMetadata(%s, %s)" % (self.file_metadata, self.log)


class FileMetadata(object):
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
        return "FileMetadata(%s, %s, %s, %s)" % (self.path, self.datatype, self.properties, self.layers)


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

        return FileMetadata(path, "data", properties, layers)

    @staticmethod
    def from_layer(layer):
        return (("description", layer.description),)


class OGRLoader(object):
    @staticmethod
    def from_file(path):
        datasource = DataSource(path)
        properties = {}
        layers = [(layer.name or None, OGRLoader.from_layer(layer)) for layer in datasource]

        return FileMetadata(path, DataTypes.data, properties, layers)

    OGR_DATATYPE_CONVERSIONS = {
        "OFTString": "String",
        "OFTReal": "Real",
        "OFTDate": "Date"
    }

    @staticmethod
    def from_layer(layer):
        return tuple((field, OGRLoader.OGR_DATATYPE_CONVERSIONS[datatype.__name__])
                     for (field, datatype) in zip(layer.fields, layer.field_types))


class ArchiveLoader(object):
    @staticmethod
    def from_file(path):
        return FileMetadata(path, DataTypes.archive, {}, [])


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
            layers = [(None, tuple((name, datatype) for name, datatype in zip(colnames, datatypes)))]

            return FileMetadata(path, DataTypes.data, properties, layers)

    @staticmethod
    def _read_normal_csv(path):
        properties = {}
        with open(path, 'rb') as f:
            try:
                has_header = csv.Sniffer().has_header(f.read(4096))
            except Exception as e:
                return FileMetadata(path, DataTypes.data, properties, [], [e])

            f.seek(0)
            layer = []
            reader = csv.reader(f)
            row = reader.next()
            if has_header:
                row_types = reader.next()
                for k, v in zip(row, row_types):
                    layer.append((k, TabularLoader._guess_type(v)))
            else:
                n = len(row)
                for col in xrange(n):
                    layer.append((None, TabularLoader._guess_type(row[col])))

            layers = [(None, tuple(layer))]

        return FileMetadata(path, DataTypes.data, properties, layers)

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

        has_netlogo_in_first_row = False
        has_netlogo_in_second_row = False
        has_ragged_columns = False

        try:
            with open(path, 'rb') as f:
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


class CodeLoader(object):
    @staticmethod
    def from_file(path):
        return FileMetadata(path, DataTypes.code, {}, [])


class DocumentLoader(object):
    @staticmethod
    def from_file(path):
        return FileMetadata(path, DataTypes.document, {}, [])


class UnknownLoader(object):
    @staticmethod
    def from_file(path):
        return FileMetadata(path, DataTypes.none, {}, [])

CONSTRUCTOR_FORMATS = {
    ArchiveLoader.from_file: frozenset([".bzip2", ".gzip", ".zip", ".7z", ".tar"]),
    # MP4Loader.from_file: frozenset([".mp4"]),
    TabularLoader.from_file: frozenset([".csv", ".tsv"]),
    OGRLoader.from_file: frozenset([".shp"]),
    GDALLoader.from_file: frozenset([".jpg", ".gif", ".png", ".asc"]),
    CodeLoader.from_file: frozenset([".r", ".java", ".py", ".pl", ".jl", ".nlogo", ".sh"]),
    DocumentLoader.from_file: frozenset([".md", ".rmd", ".ipynb", ".rtf", ".pdf", ".doc", ".docx", ".rst", ".html", ".txt"])
}

FORMAT_DISPATCH = collections.defaultdict(lambda: UnknownLoader.from_file)

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

    _, ext = path.splitext(path)
    ext = sanitize_ext(ext)
    return FORMAT_DISPATCH[ext](path)


def extract_metadata_groups(project_grouped_file_paths):
    """

    :type project_grouped_file_paths: ProjectGroupedFilePaths
    :return:
    :rtype: MetadataCollection
    """

    with cd(path.join(settings.MIRACLE_PROJECT_DIRECTORY, project_grouped_file_paths.project_token)):
        metadata_list = []
        grouped_file_paths = project_grouped_file_paths.grouped_paths
        for grouped_file_path in grouped_file_paths:
            extractor = FORMAT_DISPATCH[grouped_file_path.dispatch]
            metadata_list.append(MetadataFileGroup(grouped_file_path, extractor(grouped_file_path.group_name)))

    return MetadataCollection(project_token=project_grouped_file_paths.project_token,
                              metadata_file_groups=metadata_list,
                              paths=project_grouped_file_paths.paths)
