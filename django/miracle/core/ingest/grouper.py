"""
Explode metadata and group by column metadata
"""
from os import path
from . import (ProjectGroupedFilePaths,
            MetadataDataTableGroup, MetadataDataTable, MetadataAnalysis, MetadataProject)


class MetadataLayersInvalid(Exception):
    pass


def group_metadata(project_grouped_file_paths):
    """

    :type project_grouped_file_paths: ProjectGroupedFilePaths
    :return:
    """
    file_groups = project_grouped_file_paths.grouped_paths

    column_metadata = {}
    datatablegroups = []
    analyses = []
    for file_group in file_groups:
        if _in_data_folder(file_group):
            to_datatablegroups(file_group, column_metadata, datatablegroups)
        elif _in_src_folder(file_group):
            to_analysis(file_group, analyses)

    datatablegroups += column_metadata.values()
    return MetadataProject(project_token=project_grouped_file_paths.project_token,
                           datatablegroups=datatablegroups,
                           analyses=analyses,
                           paths=project_grouped_file_paths.paths)


def to_analysis(metadata_file_group, analyses):
    analysis = MetadataAnalysis(name=metadata_file_group.title,
                                path=metadata_file_group.group_name,
                                parameters=metadata_file_group.metadata.layers)
    analyses.append(analysis)


def to_datatablegroups(file_group, grouped_datatablegroups, datatablegroups):
    """
    Convert a metadata object into one or more datatablegroups

    Since the database relationship is currently one to many
    for DataTables and DatasetFiles, MetadataFileGroups are assumed
    to have at most one layer

    Metadata that has one or more columns with a None name is always
    placed in its own group since we do not want the metadata grouper
    to place two files in the same column group simply because they do
    not have column names and have the same number of columns

    :type file_group:
    :type grouped_datatablegroups: dict
    :type datatablegroups: list
    :return:
    """

    file_inds = file_group.inds
    layers = file_group.metadata.layers

    datatable = MetadataDataTable(path_ids=file_inds,
                                  name=file_group.title)
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


def _in_project_folder(file_group, metadata_type):
    """
    Determine whether the `file_group` is a data or code
    based on its base folder

    :type file_group: MetadataFileGroup
    :return:
    """

    name = file_group.group_name
    if path.commonprefix([metadata_type, name]):
        return True
    return False


def _in_data_folder(metadata_file_group):
    return _in_project_folder(metadata_file_group, "data")


def _in_src_folder(metadata_file_group):
    return _in_project_folder(metadata_file_group, "src")
