"""
Groups files into units for the metadata extractor

The only file type that is currently grouped is the shapefile
"""
from os import path
from collections import namedtuple, defaultdict

from .archive_extractor import ProjectFilePaths

ProjectGroupedFilePaths = namedtuple('ProjectGroupedFilePaths', ['project_token', 'grouped_paths', 'paths'])


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
