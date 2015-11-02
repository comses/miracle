import os
from os import path
import pyunpack

import shutil
import json
import yaml
import tempfile

from django.conf import settings
from django.db import transaction
from .metadata import load_metadata, ProjectMetadata, Metadata, DataTypes
from .models import Analysis, Dataset, DataTable, Project, ProjectPath, User
import utils

import logging

logger = logging.getLogger(__name__)


class MetadataFileExtractor(object):
    @staticmethod
    def to_analysis(file_analysis, projectpath):
        """
        Convert file metadata tagged with the code datatype to an Analysis

        :param file_analysis:

        :type file_analysis: Metadata
        :type project: Project

        :return: an Analysis
        :rtype: Analysis
        """
        project = projectpath.project
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

        return Analysis(name=name,
                        creator=project.creator,
                        project=project,
                        path=projectpath,
                        file_type=file_type)

    @staticmethod
    def to_dataset(file_dataset, projectpath):
        """
        Convert file metadata tagged with the data datatype to a Dataset and set of DataTables

        :type file_dataset: Metadata
        :type project: Project

        :rtype: Dataset
        """
        project = projectpath.project
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

    @staticmethod
    def dataset_metadata_already_exists(metadata):
        # TODO: add method for checking if metadata already exists
        pass

    @classmethod
    def extract_file_metadata(cls, projectpath, projects_folder = settings.MIRACLE_PROJECT_DIRECTORY):
        project = projectpath.project
        filepath = path.join(projects_folder, project.path, str(projectpath.filepath))
        metadata = load_metadata(filepath)
        if metadata.datatype == DataTypes.code:
            analysis = cls.to_analysis(metadata, projectpath)
            analysis.save()
            return analysis
        elif metadata.datatype == DataTypes.data:
            dataset = cls.to_dataset(metadata, projectpath)
            dataset.save()
            return dataset
        else:
            logger.info("no metadata extracted for file {}".format(filepath))
            return None


    @staticmethod
    def to_datatable(file_dataset, dataset):
        base_dir, filename = os.path.split(file_dataset.path)
        name, ext = os.path.splitext(filename)

        return DataTable(name=name,
                         creator=dataset.creator,
                         datafile=file_dataset.path,
                         dataset=dataset)


class Packrat(object):

    def __init__(self, token, tmpfolder, status=None, paths=[]):
        self.status = status
        self.token = token
        self.paths = paths
        self.tmpfolder = tmpfolder

    def __bool__(self):
        return self.status is None

    __nonzero__ = __bool__

    @classmethod
    def root_is_not_unique(cls, token, tmpfolder, files):
        return cls(token=token,
                   status="root folder is not unique. contains {}".format(files.__str__()),
                   tmpfolder=tmpfolder)

    @classmethod
    def root_is_not_folder(cls, token, tmpfolder, root):
        return cls(token=token,
                   status="root {} is nat a folder".format(root),
                   tmpfolder=tmpfolder)

    @classmethod
    def no_packrat_folder(cls, token, tmpfolder):
        return cls(token=token,
                   status="no packrat folder",
                   tmpfolder=tmpfolder)

    @classmethod
    def no_token_folder(cls, token, tmpfolder):
        return cls(token=token,
                   status="no project folder named {} exists".format(token),
                   tmpfolder=tmpfolder)

    @classmethod
    def unpacking_failure(cls, token, tmpfolder, status):
        return cls(token=token, status=status, tmpfolder=tmpfolder)

    @staticmethod
    def _extract_files(folder):
        fnames_list = []
        for (parent_dir, dirnames, fnames) in os.walk(folder):
            for fname in fnames:
                file_path = path.relpath(
                    path.join(parent_dir, fname),
                    folder)
                fnames_list.append(file_path)
        return fnames_list

    @staticmethod
    def _move_project_to_projects(folder, projects_folder):
        token = path.basename(folder)
        dest = path.join(path.expanduser(projects_folder), token)
        shutil.move(folder, dest)
        return dest

    @staticmethod
    def _unpack(archive):
        """
        Extract archive into tmpdir

        :param archive:
        :type archive: str
        :return:
        """
        archive_dir, archive_name = path.split(archive)
        with utils.Chdir(archive_dir):
            tempdir = tempfile.mkdtemp()
            pyunpack.Archive(archive_name).extractall(tempdir)

        return tempdir

    @staticmethod
    def _add_paths(project, paths):
        db_paths = []
        with transaction.atomic():
            for path in paths:
                db_path = ProjectPath.objects.create(filepath=path, project=project)
                db_paths.append(db_path)
        return db_paths

    def cleanup(self):
        shutil.rmtree(self.tmpfolder)

    @classmethod
    def _get_and_add_paths(cls, project, token, project_folder):
        project_folder_src = path.join(project_folder, token)
        paths = cls._extract_files(project_folder_src)
        db_paths = cls._add_paths(project, paths)
        return project_folder_src, db_paths


    @classmethod
    def extract(cls, project, archive, projects_folder = settings.MIRACLE_PROJECT_DIRECTORY):

        token = project.path
        try:
            tmpfolder = cls._unpack(archive)
        except Exception, e:
            logger.error(e)
            return cls.unpacking_failure(e, tmpfolder)

        files = os.listdir(tmpfolder)
        if len(files) != 1:
            return cls.root_is_not_unique(token, tmpfolder, files)

        project_folder = path.join(tmpfolder, files[0])
        if not path.isdir(project_folder):
            return cls.root_is_not_folder(project_folder, tmpfolder)

        contents = os.listdir(project_folder)
        if "packrat" not in contents:
            return cls.no_packrat_folder(token, tmpfolder)
        if token not in contents:
            return cls.no_token_folder(token, tmpfolder)

        project_folder_src, db_paths = cls._get_and_add_paths(project, token, project_folder)
        try:
            cls._move_project_to_projects(project_folder_src, projects_folder)
        except Exception, e:
            logger.error(e)
            return cls.unpacking_failure(token = token,
                                         status = "Error on file movement. Contact administrator.",
                                         tmpfolder = tmpfolder)

        return cls(token = token, paths = db_paths, tmpfolder = tmpfolder)
