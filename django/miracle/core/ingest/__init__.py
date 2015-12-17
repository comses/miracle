from collections import namedtuple
from enum import Enum

ProjectFilePaths = namedtuple('ProjectFilePath', [
    'project_token',    # unique project slug
    'paths'             # list of all paths contained in the archive
])

ProjectGroupedFilePaths = namedtuple('ProjectGroupedFilePaths', [
    'project_token',
    'grouped_paths',    # metadata entries for a group of files
    'paths'
])

DataTypes = Enum('DataTypes', 'none archive code data document vizualization')

MetadataDataTable = namedtuple('MetadataDataTable', [
    'path_ids',
    'name'
])

MetadataDataTableGroup = namedtuple('MetadataDataTableGroup', [
    'name',
    'properties',
    'datatables'
])

MetadataAnalysis = namedtuple('MetadataAnalysis', [
    'name',
    'path'
])

MetadataProject = namedtuple('MetadataProject', [
    'project_token',
    'datatablegroups',
    'analyses',
    'paths'
])

class PackratException(Exception):
    pass
