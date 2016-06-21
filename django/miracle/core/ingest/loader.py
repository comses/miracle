"""
Load metadata extracted from a project archive into the database
"""

import logging
import requests

from os import path
from django.conf import settings
from django.db import transaction

from . import MetadataAnalysis, MetadataDataTableGroup, MetadataProject
from ..deployr import login, DeployrAPI, response200orError
from ..models import DataAnalysisScript, DataTableGroup, Project, DataFile, DataColumn
from .. import utils

logger = logging.getLogger(__name__)


def load_datatablegroups(metadata_datatablegroups, project):
    for metadata_datatablegroup in metadata_datatablegroups:
        load_datatablegroup(metadata_datatablegroup, project)


def load_datatablegroup(metadata_datatablegroup, project):
    """
    Convert file metadata tagged with the data datatype to a DataTableGroup and set of DataTables

    :type metadata_datatablegroup: MetadataDataTableGroup
    :type datatablegroupfiles: list[DataFile]

    :rtype: DataTableGroup
    """

    datatablegroup = DataTableGroup.objects.create_data_group(name=metadata_datatablegroup.name, project=project)
    load_datatablegroup_columns(metadata_datatablegroup.properties, datatablegroup)
    datafiles = []
    for metadata_datafile in metadata_datatablegroup.datafiles:
        datatable = load_datafile(metadata_datafile, datatablegroup)
        datafiles.append(datatable)
    datatablegroup.tables = datafiles
    logger.debug("ADDED DATATABLE GROUP: {}".format(datatablegroup.name))


def load_datatablegroup_columns(metadata_columns, datatablegroup):
    columns = []
    for (table_order, metadata) in enumerate(metadata_columns, start=1):
        name, data_type = metadata
        columns.append(
            DataColumn(name=name or "",
                       data_table_group=datatablegroup,
                       table_order=table_order,
                       data_type=data_type)
        )
    DataColumn.objects.bulk_create(columns)


def load_datafile(metadata_datafile, datatablegroup):
    datafile = DataFile.objects.create(data_table_group=datatablegroup,
                                       project=datatablegroup.project,
                                       archived_file=metadata_datafile.path)
    return datafile


def load_analysis(metadata_analysis, project):
    """
    Convert raw analysis metadata to an appropriately parameterized DataAnalysisScript

    :param metadata_analysis:

    :type metadata_analysis: MetadataAnalysis
    :type project: Project

    :return: an Analysis
    :rtype: Analysis
    """
    base_dir, filename = path.split(metadata_analysis.path)
    name, ext = path.splitext(filename)
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

    data_analysis_script = project.analyses.create(name=metadata_analysis.name,
                                                   creator=project.creator,
                                                   archived_file=metadata_analysis.path,
                                                   file_type=file_type,
                                                   enabled=True)
    data_analysis_script.add_parameters(metadata_analysis.parameters)


def load_analyses(metadata_analyses, project):
    """Load analyses into database"""
    for metadata_analysis in metadata_analyses:
        load_analysis(metadata_analysis, project)


def load_deployr(metadata_analyses, project):
    """Load analyses into deployr and make deployr project"""
    try:
        with login() as session:
            response = DeployrAPI.create_working_directory(project.slug, session)
            response200orError(response)
        for metadata_analysis in metadata_analyses:
            response = DeployrAPI.upload_script(metadata_analysis.path,
                                                project.slug,
                                                session)
            response200orError(response)
    except requests.exceptions.ConnectionError:
        logger.exception(
            "CONNECTION ERROR: the deployr server must be running and have a user " +
            "matching the deployr username (DEFAULT_DEPLOYR_USER) and password (DEFAULT_DEPLOYR_PASSWORD)")
        raise


def load_project(metadata_project):
    """
    Load all the extracted file metadata into the database

    :type metadata_project: MetadataProject
    """

    metadata_analyses = metadata_project.analyses
    metadata_datatablegroups = metadata_project.datatablegroups
    project = Project.objects.get(slug=metadata_project.project_token)

    with transaction.atomic():
        load_analyses(metadata_analyses, project)
        load_datatablegroups(metadata_datatablegroups, project)
        with utils.Chdir(project.project_path):
            load_deployr(metadata_analyses, project)
