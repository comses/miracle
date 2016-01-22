from collections import namedtuple
from enum import Enum

ProjectFilePaths = namedtuple('ProjectFilePaths', [
    'project_token',    # unique project slug
    'paths'             # list of all paths contained in the archive
])

ProjectGroupedFilePaths = namedtuple('ProjectGroupedFilePaths', [
    'project_token',
    'grouped_paths',    # metadata entries for a group of files
    'paths'
])

DataTypes = Enum('DataTypes', 'none archive code data document vizualization')

MetadataDataFile = namedtuple('MetadataDataFile', [
    'name',
    'path'
])

MetadataDataTableGroup = namedtuple('MetadataDataTableGroup', [
    'name',
    'properties',
    'datafiles'
])

MetadataAnalysis = namedtuple('MetadataAnalysis', [
    'name',
    'path',
    'parameters'
])

MetadataProject = namedtuple('MetadataProject', [
    'project_token',
    'datatablegroups',
    'analyses'
])

class PackratException(Exception):
    pass
