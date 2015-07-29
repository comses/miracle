"""
Interface to the metadata extraction tools in metadata.py and extractors.py

The classes and functions located in extractors.py and metadata.py should not
be called directly.
"""

import shutil
from os import path
from .models import Analysis, Dataset, DataTable, DataTableColumn, User, Project
from .metadata import Metadata, load_metadata
from .extractors import Extractor
from ..settings import MIRACLE_ANALYSIS_DIRECTORY


def process_uploaded_analysis(fullpath, project, creator):
    """
    Process an uploaded archive. Extracts the archive to the appropriate folder
    and extracts metadata from the archive

    :param fullpath: absolute path to the uploaded file
    :param project: project you want to associate the analysis with
    :param creator: user you want to associate the analysis with

    :type fullpath: str
    :type project: Project
    :type creator: User

    :return:
    """
    analysis = Analysis(name=path.basename(fullpath),
                        project=project,
                        data_path=fullpath)
    analysis.save()
    extract = Extractor.from_archive(fullpath, analysis_name=str(analysis.id))
    analysis_metadata = extract.extract_metadata()
    dataset_metadata = analysis_metadata.dataset_metadata
    for ds in dataset_metadata:
        _upload_dataset_metadata_to_db(ds, [analysis], project, creator)


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
    _move_dataset_to_analysis(fullpath, analysis_name, copy)


def _move_dataset_to_analysis(fullpath_dataset, analysis_name, copy=False):
    filename = path.basename(fullpath_dataset)
    dest_folder = path.join(MIRACLE_ANALYSIS_DIRECTORY,
                     analysis_name,
                     "data")
    if path.exists(dest_folder):
        shutil.move(fullpath_dataset, path.join(dest_folder, filename))
    else:
        dest = path.join(MIRACLE_ANALYSIS_DIRECTORY,
                         analysis_name,
                         filename)
        if copy:
            shutil.copy(fullpath_dataset, dest)
        else:
            shutil.move(fullpath_dataset, dest)


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