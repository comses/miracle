"""
Interface to the metadata extraction tools in metadata.py and extractors.py

The classes and functions located in extractors.py and metadata.py should not
be called directly.
"""
# TODO: Update or Remove Interface

import shutil
from os import path
from django.conf import settings
from .models import Analysis, Dataset, DataTable, DataTableColumn, User, Project
from .metadata import Metadata, load_metadata, DataTypes
from .extractors import Extractor

def process_project(project_name, metadata, creator):
    """
    Process an uploaded archive. Extracts the archive to the appropriate folder
    and extracts metadata from the archive

    :param project_name: project you want to associate the analysis with
    :param creator: user you want to associate the analysis with

    :type project_name: str
    :type creator: User

    :return:
    """
    project = Project.objects.create(
        creator=creator,
        name=project_name)

    dataset_metadata = [item for item in metadata if item.datatype == DataTypes.code]
    analysis_metadata = metadata.analyses
    for dataset in dataset_metadata:
        _upload_dataset_metadata_to_db(dataset, [], project, creator)
    for analysis in analysis_metadata:
        _upload_analysis_metadata_to_db(analysis, project, creator)


def process_uploaded_dataset(fullpath, analysis, project, creator, copy=False):
    """
    Extract metadata from an uploaded dataset. Move the dataset to the
    appropriate location. Not possible to use for a dataset that has
    multiple files associated with it (such as a Shapefile).

    :param fullpath: absolute path to the uploaded file
    :param analysis: analysis you want to associate the dataset with
    :param project: project you want to associate the dataset with
    :param creator: user you want to associate the analysis with

    :type fullpath: str
    :type analysis: Analysis
    :type project: Project
    :type creator: User

    :return:
    """
    metadata = load_metadata(fullpath)
    _upload_dataset_metadata_to_db(metadata, [analysis], project, creator)
    analysis_name = str(analysis.id)

def process_uploaded_analysis(fullpath, project, creator, copy=False):
    """
    Extract metadata from an uploaded analysis. Move the analysis to the
    appropriate location.

    :param fullpath: absolute path to the uploaded file
    :param project: project you want to associate the analysis with
    :param creator: user you want to associate the analysis with
    :param copy: should the analysis be copied or moved?

    :type fullpath: str
    :type project: Project
    :type creator: User

    :return:
    """
    pass

def _move_item_to_project(fullpath, project_name, copy=False):
    filename = path.basename(fullpath)
    dest_folder = path.join(settings.MIRACLE_PROJECT_DIRECTORY,
                            project_name,
                            "data")
    if path.exists(dest_folder):
        shutil.move(fullpath, path.join(dest_folder, filename))
    else:
        dest = path.join(settings.MIRACLE_PROJECT_DIRECTORY,
                         project_name,
                         filename)
        if copy:
            shutil.copy(fullpath, dest)
        else:
            shutil.move(fullpath, dest)

def _upload_analysis_metadata_to_db(metadata, project, creator):
    pass

def _upload_dataset_metadata_to_db(metadata, analyses, project, creator):
    datapath = metadata.path
    datatype = metadata.datatype
    properties = metadata.properties
    layers = metadata.layers

    dataset = Dataset(name=path.basename(datapath),
                      project=project,
                      data_type=datatype,
                      creator=creator,
                      properties=properties)
    dataset.save()
    dataset.analyses = analyses

    for layer in layers:
        _upload_datatable_metadata_to_db(layer, dataset, creator)


def _upload_datatable_metadata_to_db(layer, dataset, creator):
    datatable = DataTable(name="ex",
                          dataset=dataset,
                          creator=creator)
    datatable.save()

    for colname, datatype in layer.iteritems():
        datatablecolumn = DataTableColumn(name=colname,
                                          datatable=datatable,
                                          data_type=datatype)
        datatablecolumn.save()
