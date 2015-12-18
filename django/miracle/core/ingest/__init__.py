from collections import namedtuple
from enum import Enum

ProjectFilePaths = namedtuple('ProjectFilePath', [
    'project_token',    # unique project slug
    'paths'             # list of all paths contained in the archive
])

ProjectGroupedFilePaths = namedtuple('ProjectGroupedFilePaths', [
    'project_token',
    'grouped_paths',
    'paths'
])

MetadataCollection = namedtuple('MetadataCollection', [
    'project_token',
    'metadata_file_groups',
    'paths'
])

MetadataFileGroup = namedtuple('MetadataFileGroup', [
    'group',
    'metadata'
])

DataTypes = Enum('DataTypes', 'none archive code data document vizualization')


class PackratException(Exception):
    pass
