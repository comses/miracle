"""
Explode metadata and group by column metadata
"""
from os import path
from collections import namedtuple
from .filegroup_extractors import MetadataCollection, MetadataFileGroup

MetadataDataTable = namedtuple('MetadataDataTable', ['path_ids', 'name'])
MetadataDataTableGroup = namedtuple('MetadataDataTableGroup', ['name', 'properties', 'datatables'])
MetadataAnalysis = namedtuple('MetadataAnalysis', ['name', 'path'])
GroupedMetadata = namedtuple('GroupedMetadata', ['project_token', 'datatablegroups', 'analyses', 'paths'])


class MetadataLayersInvalid(Exception):
    pass


def group_metadata(metadata_collection):
    """

    :type metadata_collection: MetadataCollection
    :return:
    """
    metadata_file_groups = metadata_collection.metadata_file_groups

    column_metadata = {}
    datatablegroups = []
    analyses = []
    for metadata_file_group in metadata_file_groups:
        if _in_data_folder(metadata_file_group):
            to_datatablegroups(metadata_file_group, column_metadata, datatablegroups)
        elif _is_analysis(metadata_file_group):
            to_analysis(metadata_file_group, analyses)

    datatablegroups += column_metadata.values()
    return GroupedMetadata(project_token=metadata_collection.project_token,
                           datatablegroups=datatablegroups,
                           analyses=analyses,
                           paths=metadata_collection.paths)


def to_analysis(metadata_file_group, analyses):
    analysis = MetadataAnalysis(name=metadata_file_group.group.title,
                                path=metadata_file_group.group.group_name)
    analyses.append(analysis)


def to_datatablegroups(metadata_file_group, grouped_datatablegroups, datatablegroups):
    """
    Convert a metadata object into one or more datatablegroups

    Since the database relationship is currently one to many
    for DataTables and DatasetFiles, MetadataFileGroups are assumed
    to have at most one layer

    Metadata that has one or more columns with a None name is always
    placed in its own group since we do not want the metadata grouper
    to place two files in the same column group simply because they do
    not have column names and have the same number of columns

    :type metadata_file_group: MetadataFileGroup
    :type grouped_datatablegroups: dict
    :type datatablegroups: list
    :return:
    """

    file_inds = metadata_file_group.group.inds
    layers = metadata_file_group.metadata.layers

    datatable = MetadataDataTable(path_ids=file_inds,
                                  name=metadata_file_group.group.title)
    if len(layers) >= 1:
        column_info = layers[0][1]

        if _has_all_valid_column_names(column_info):
            has_layer = column_info in grouped_datatablegroups
            if has_layer:
                datatablegroup = grouped_datatablegroups[column_info]
                datatablegroup.datatables.append(datatable)
            else:
                datatablegroup = MetadataDataTableGroup(properties=column_info,
                                                        datatables=[datatable],
                                                        name=datatable.name)
                grouped_datatablegroups[column_info] = datatablegroup
        else:
            datatablegroup = MetadataDataTableGroup(properties=column_info,
                                                    datatables=[datatable],
                                                    name=datatable.name)
            datatablegroups.append(datatablegroup)
    else:
        datatablegroup = MetadataDataTableGroup(properties=tuple(),
                                                datatables=[datatable],
                                                name=datatable.name)
        datatablegroups.append(datatablegroup)


def _has_all_valid_column_names(columns):
    for (cname, ctype) in columns:
        if cname is None:
            return False

    return True


def _in_project_folder(metadata_file_group, metadata_type):
    """
    Determine whether the `metadata_file_group` is a data or code
    based on its base folder

    :type metadata_file_group: MetadataFileGroup
    :return:
    """

    name = metadata_file_group.group.group_name
    if path.commonprefix([metadata_type, name]):
        return True
    return False


def _in_data_folder(metadata_file_group):
    return _in_project_folder(metadata_file_group, "data")


def _is_analysis(metadata_file_group):
    return _in_project_folder(metadata_file_group, "src") or \
           _in_project_folder(metadata_file_group, "apps") or \
           _in_project_folder(metadata_file_group, "doc")
