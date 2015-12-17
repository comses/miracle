"""
Load metadata extracted from a project archive into the database
"""

import json
import logging

import os
from os import path
from django.conf import settings
from django.db import transaction

from .filegroup_extractors import extract_metadata, Metadata, DataTypes
from .metadatagrouper import MetadataAnalysis, MetadataDataTableGroup, GroupedMetadata
from .models import DataAnalysisScript, Dataset, DataTable, Project, DatasetFile, DataTableColumn

logger = logging.getLogger(__name__)


def load_datatablegroupfiles(grouped_metadata, project):
    """
    :type grouped_metadata: GroupedMetadata
    """
    datasetfiles = [DatasetFile(project=project, archived_file=file_path) for file_path in grouped_metadata.paths]

    # bulk_create does not work here because we need the datasetfile ids
    for datasetfile in datasetfiles:
        datasetfile.save()
    return datasetfiles


def load_datatablegroups(metadata_datatablegroups, project, datatablegroupfiles):
    for metadata_datatablegroup in metadata_datatablegroups:
        load_datatablegroup(metadata_datatablegroup, project, datatablegroupfiles)


def load_datatablegroup(metadata_datatablegroup, project, datatablegroupfiles):
    """
    Convert file metadata tagged with the data datatype to a Dataset and set of DataTables

    :type metadata_datatablegroup: MetadataDataTableGroup
    :type datatablegroupfiles: list[DatasetFile]

    :rtype: Dataset
    """

    datatablegroup = Dataset.objects.create(name=metadata_datatablegroup.name,
                                            creator=project.creator,
                                            project=project)
    load_datatablegroup_columns(metadata_datatablegroup.properties, datatablegroup)
    datatables = []
    for metadata_datatable in metadata_datatablegroup.datatables:
        datatable = load_datatable(metadata_datatable, datatablegroupfiles, datatablegroup)
        datatables.append(datatable)

    datatablegroup.tables = datatables
    logger.debug("added datatablegroup {}".format(metadata_datatable.name))


def load_datatablegroup_columns(metadata_columns, datatablegroup):
    DataTableColumn.objects.bulk_create(
        DataTableColumn(name=name or "",
                        dataset=datatablegroup,
                        data_type=data_type) for (name, data_type) in metadata_columns
    )


def load_datatable(metadata_datatable, datasetfiles, datatablegroup):
    related_datasetfiles = [datasetfiles[id] for id in metadata_datatable.path_ids]
    datatable = DataTable.objects.create(name=metadata_datatable.name,
                                         dataset=datatablegroup)
    datatable.files = related_datasetfiles
    return datatable


def to_analysis(metadata_analysis, project):
    """
    Convert analysis metadata to an Analysis

    :param metadata_analysis:

    :type metadata_analysis: MetadataAnalysis
    :type project: Project

    :return: an Analysis
    :rtype: Analysis
    """
    base_dir, filename = os.path.split(metadata_analysis.path)
    name, ext = os.path.splitext(filename)
    ext = ext.lower()

    file_type = ""
    if ext == ".jl":
        file_type = "Julia"
    elif ext == ".r":
        file_type = "R"
    elif ext == ".py":
        file_type = "Python"
    elif ext == ".pl":
        file_type = "Perl"

    return DataAnalysisScript(name=metadata_analysis.name,
                              creator=project.creator,
                              project=project,
                              archived_file=metadata_analysis.path,
                              file_type=file_type)


def load_analyses(metadata_analyses, project):
    analyses = [to_analysis(metadata_analysis, project) for metadata_analysis in metadata_analyses]
    for analysis in analyses:
        analysis.save()
    #DataAnalysisScript.objects.bulk_create(analyses)


def load_project(grouped_metadata):
    """
    Load all the extracted file metadata into the database
    """

    metadata_analyses = grouped_metadata.analyses
    metadata_datatablegroups = grouped_metadata.datatablegroups

    project = Project.objects.filter(name=grouped_metadata.project_token).first()

    with transaction.atomic():
        datatablegroupfiles = load_datatablegroupfiles(grouped_metadata, project)
        load_analyses(metadata_analyses, project)
        load_datatablegroups(metadata_datatablegroups, project, datatablegroupfiles)
