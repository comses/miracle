"""
Load metadata extracted from a project archive into the database
"""

import json
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


def load_datatablegroupfiles(grouped_metadata, project):
    """
    :type grouped_metadata: GroupedMetadata
    """
    datasetfiles = [DataFile(project=project, archived_file=file_path) for file_path in grouped_metadata.paths]

    # bulk_create does not work here because we need the DataFile ids
    for datasetfile in datasetfiles:
        datasetfile.save()
    return datasetfiles


def load_datatablegroups(metadata_datatablegroups, project, datatablegroupfiles):
    for metadata_datatablegroup in metadata_datatablegroups:
        load_datatablegroup(metadata_datatablegroup, project, datatablegroupfiles)


def load_datatablegroup(metadata_datatablegroup, project, datatablegroupfiles):
    """
    Convert file metadata tagged with the data datatype to a DataTableGroup and set of DataTables

    :type metadata_datatablegroup: MetadataDataTableGroup
    :type datatablegroupfiles: list[DataFile]

    :rtype: DataTableGroup
    """

    datatablegroup = DataTableGroup.objects.create_data_group(name=metadata_datatablegroup.name, project=project)
    load_datatablegroup_columns(metadata_datatablegroup.properties, datatablegroup)
    """ FIXME: Calvin, is there any essential work going on here?"""
    datatables = []
    for metadata_datatable in metadata_datatablegroup.datatables:
        datatable = load_datatable(metadata_datatable, datatablegroupfiles, datatablegroup)
        datatables.append(datatable)
    datatablegroup.tables = datatables
    logger.debug("ADDED DATATABLE GROUP: {}".format(metadata_datatable.name))


def load_datatablegroup_columns(metadata_columns, datatablegroup):
    DataColumn.objects.bulk_create(DataColumn(name=name or "",
                                              data_table_group=datatablegroup,
                                              data_type=data_type) for (name, data_type) in metadata_columns
                                   )


def load_datatable(metadata_datatable, datasetfiles, datatablegroup):
    related_datasetfiles = [datasetfiles[id] for id in metadata_datatable.path_ids]
    datatable = DataFile.objects.create(data_table_group=datatablegroup,
                                        project=datatablegroup.project)
    datatable.files = related_datasetfiles
    return datatable


def load_analysisparameter(dataanalysis_script, parameter):
    """
    :type dataanalysis_script: DataAnalysisScript
    :type parameter: dict
    :return:
    """
    misc = {}
    if parameter.has_key("valueList"):
        misc["valueList"] = parameter["valueList"]
    if parameter.has_key("valueRange"):
        misc["valueRange"] = parameter["valueRange"]

    dataanalysis_script.parameters.create(
        name=parameter["name"],
        label=parameter["label"],
        data_type=parameter["render"],
        default_value=str(parameter["default"]),
        misc=misc
    )


def load_analysisparameters(dataanalysis_script, parameters):
    for parameter in parameters:
        load_analysisparameter(dataanalysis_script, parameter)


def load_analysis(metadata_analysis, project):
    """
    Convert analysis metadata to an Analysis

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

    dataanalysis_script = DataAnalysisScript(name=metadata_analysis.name,
                                             creator=project.creator,
                                             project=project,
                                             archived_file=metadata_analysis.path,
                                             file_type=file_type)
    dataanalysis_script.save()
    load_analysisparameters(dataanalysis_script, metadata_analysis.parameters)


def load_analyses(metadata_analyses, project):
    """Load analyses into database"""
    for metadata_analysis in metadata_analyses:
        load_analysis(metadata_analysis, project)


def load_deployr(metadata_analyses, project):
    """Load analyses into deployr and make deployr project"""
    try:
        with login() as session:
            response = DeployrAPI.create_working_directory(project.name, session)
            response200orError(response)
        for metadata_analysis in metadata_analyses:
            response = DeployrAPI.upload_script(metadata_analysis.path,
                                                project.name,
                                                session)
            response200orError(response)
    except requests.exceptions.ConnectionError as e:
        logger.exception(e)
        logger.debug(
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

    project = Project.objects.filter(name=metadata_project.project_token).first()

    with transaction.atomic():
        datatablegroupfiles = load_datatablegroupfiles(metadata_project, project)
        load_analyses(metadata_analyses, project)
        load_datatablegroups(metadata_datatablegroups, project, datatablegroupfiles)
        with utils.Chdir(path.join(settings.MIRACLE_PROJECT_DIRECTORY, project.slug)):
            load_deployr(metadata_analyses, project)
