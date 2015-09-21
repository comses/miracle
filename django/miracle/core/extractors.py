import os
import pyunpack

import shutil
import collections
import json
import yaml

from django.conf import settings
from .metadata import load_metadata, ProjectMetadata, Metadata, DataTypes
from .models import Analysis, Dataset, DataTable, Project, User

import logging

logger = logging.getLogger(__name__)


class MetaDataImportError(Exception):
    pass


def to_analysis(file_analysis, project):
    """
    Convert file metadata tagged with the code datatype to an Analysis

    :param file_analysis:

    :type file_analysis: Metadata
    :type project: Project

    :return: an Analysis
    :rtype: Analysis
    """
    base_dir, filename = os.path.split(file_analysis.path)
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

    uploaded_file = file_analysis.path
    return Analysis(name=name,
                    creator=project.creator,
                    project=project,
                    file_type=file_type,
                    uploaded_file=uploaded_file)


def to_dataset(file_dataset, project):
    """
    Convert file metadata tagged with the data datatype to a Dataset and set of DataTables

    :type file_dataset: Metadata
    :type project: Project
    """
    base_dir, filename = os.path.split(file_dataset.path)
    name, ext = os.path.splitext(filename)
    ext = ext.lower()

    data_type = ext
    properties = json.dumps(
        { "properties": file_dataset.properties
        , "layers": file_dataset.layers })

    return Dataset(name=name,
                   creator=project.creator,
                   project=project,
                   data_type=data_type,
                   properties=properties)


def to_datatable(file_dataset, dataset):
    base_dir, filename = os.path.split(file_dataset.path)
    name, ext = os.path.splitext(filename)

    return DataTable(name=name,
                     creator=dataset.creator,
                     datafile=file_dataset.path,
                     dataset=dataset)


def to_project_from_file(project_metadata, dataset_groupings_file, creator):
    f = open(dataset_groupings_file)
    dataset_groups = yaml.safe_load(f)['datasets']
    f.close()
    return to_project(project_metadata, dataset_groups, creator)


def to_project(project_metadata, dataset_groups, creator):
    project_name = project_metadata.name
    project = Project.objects.create(name=project_metadata.name, creator=creator)
    # check the file paths
    datatable_path_to_dataset_name = {}
    for dataset_group in dataset_groups:
        name = dataset_group['name']
        paths = dataset_group['instances']
        for path in paths:
            key_path = os.path.join(project_name, "data", project_name,
                                    os.path.normpath(path))
            datatable_path_to_dataset_name[key_path] = name


    analyses = []
    datasets = {}
    for f in project_metadata.file_metadata:
        if f.datatype == DataTypes.code:
            analysis = to_analysis(f, project)
            analysis.save()
            analyses.append(analysis)

        elif f.datatype == DataTypes.data:
            path = f.path
            if datatable_path_to_dataset_name.has_key(path):

                name = datatable_path_to_dataset_name[path]
                if not datasets.has_key(name):
                    dataset = to_dataset(f, project)
                    dataset.save()

                    datatable = to_datatable(f, dataset)
                    datatable.save()

                    datasets[name] = dataset
                else:
                    datatable = to_datatable(f, datasets[name])
                    datatable.save()

            else:
                dataset = to_dataset(f, project)
                dataset.save()

                datatable = to_datatable(f, dataset)
                datatable.save()

    project.analyses = analyses
    project.datasets = datasets.values()
    project.save()
    return project


class Extractor(object):
    """
    Create one extractor per uploaded analysis
    """
    ARCHIVE_FORMATS = [".7z", ".zip"]

    def __init__(self, project_name, project_path, metadata):
        self.project_path = project_path
        self.project_name = project_name
        self.metadata = metadata

    @staticmethod
    def from_archive(fullpath,
                     project_path=settings.MIRACLE_PROJECT_DIRECTORY,
                     destroy_tmp=True,
                     overwrite=True):
        """
        Extracts an archive to a new folder

        :param fullpath: absolute path to where the project archive was
                         uploaded
        :return: path to extracted analysis
        :raises: ValueError: unsupported archive format
        :raises: NameError: project_name already exists
        """
        logger.debug("project_path: {}".format(project_path))


        directory, filename = os.path.split(fullpath)
        project_name, ext = os.path.splitext(filename)
        if overwrite:
            Extractor.delete_projects(project_name)

        if ext not in Extractor.ARCHIVE_FORMATS:
            raise ValueError("{} format not supported".format(ext))

        tmp_project_directory = os.path.join(directory, project_name)
        logger.debug("tmp_project_directry: {}".format(tmp_project_directory))
        if destroy_tmp:
            shutil.rmtree(tmp_project_directory, ignore_errors=True)

        if not os.path.exists(tmp_project_directory):
            pyunpack.Archive(fullpath).extractall(tmp_project_directory, auto_create_dir=True)
        else:
            raise NameError("'{}' already exists. Try a different name.".format(project_name))
        logger.debug("Extracted Archive")
        Extractor.cleanup(tmp_project_directory)
        metadata = Extractor.extract_metadata(tmp_project_directory)
        logger.debug("Extracted Metadata")
        Extractor.move_project(tmp_project_directory, project_path)

        if destroy_tmp:
            shutil.rmtree(tmp_project_directory)

        return Extractor(project_name, project_path, metadata)

    @staticmethod
    def delete_projects(name):
        search_dirs = ['apps', 'docs', 'data', 'output', 'src']
        for d in search_dirs:
            path = os.path.join(settings.MIRACLE_PROJECT_DIRECTORY, d, name)
            if os.path.exists(path):
                shutil.rmtree(path)

    @staticmethod
    def move_project(fullpath, project_path):
        """
        Move the extracted project at `fullpath` to `project_path`
        """
        directory, project_name = os.path.split(fullpath)

        dirs = [f for f in os.listdir(fullpath) if f in ['apps', 'docs', 'data', 'output', 'src']]
        dirs = [d for d in dirs if os.path.exists(os.path.join(fullpath, d, project_name))]
        for d in dirs:
            shutil.copytree(os.path.join(fullpath, d, project_name),
                            os.path.join(project_path, d, project_name))


    @staticmethod
    def cleanup(tmp_project_directory):
        """
        Move all analysis files up one directory, if only one subdirectory
        """
        dirs = os.listdir(tmp_project_directory)
        if "__MACOSX" in dirs:
            dirs.remove("__MACOSX")
        if len(dirs) == 1:
            directory = dirs[0]
            files = os.listdir(os.path.join(tmp_project_directory, directory))

            for file in files:
                shutil.move(os.path.join(tmp_project_directory, directory, file),
                            os.path.join(tmp_project_directory, file))

            os.rmdir(os.path.join(tmp_project_directory, directory))

    @staticmethod
    def extract_metadata(fullpath):
        """
        Create metadata from the extracted archive

        :return: metadata for the analysis and all its datasets
        :rtype: ProjectMetadata
        """

        base_dir, start_dir = os.path.split(fullpath)
        os.chdir(base_dir)
        walker = os.walk(fullpath)
        base_dir, name = os.path.split(fullpath)

        metadata = []
        log = []
        for root, dirs, files in walker:
            rel_root = os.path.relpath(root, base_dir)
            files = [f for f in files if not f[0] == '.']
            dirs[:] = [d for d in dirs if not d[0] == '.']
            for rel_file_path in files:
                fullpath = os.path.join(rel_root, rel_file_path)
                metadata.append(load_metadata(fullpath))

        return ProjectMetadata(name, metadata, log)