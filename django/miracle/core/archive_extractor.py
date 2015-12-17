from os import path
import os
import shutil
import pyunpack
import utils
import tempfile
from collections import namedtuple

from django.conf import settings

from .models import Project


class PackratException(Exception):
    pass


ProjectFilePaths = namedtuple('ProjectFilePath', ['project_token', 'paths'])


def extract(project, archive, projects_folder=settings.MIRACLE_PROJECT_DIRECTORY):
    """
    Extract a project archive into the project folder

    :param project: a project to associate the archive with
    :type project: Project
    :param archive: a path to an archive file
    :type archive: str
    :param projects_folder: the directory where the projects are stored
    :type projects_folder: str

    :return: a packrat object with the project token and the projectpath db records
    :rtype: FilePathExtractor
    """

    tmpfolder = tempfile.mkdtemp()
    token = project.name
    try:
        _unpack(archive, tmpfolder)

        files = os.listdir(tmpfolder)
        if len(files) != 1:
            raise PackratException("root folder is not unique. contains {}".format(files.__str__()))

        project_folder = path.join(tmpfolder, files[0])
        if not path.isdir(project_folder):
            raise PackratException("root {} is nat a folder".format(projects_folder))

        project_folder_contents = os.listdir(project_folder)
        if "packrat" not in project_folder_contents:
            raise PackratException("no Packrat folder")
        if token not in project_folder_contents:
            raise PackratException("no project folder named {} exists".format(token))

        _validate_project_structure(project_folder, token)
        project_folder_src, paths = _get_and_add_paths(project, token, project_folder)
        _move_project_to_projects(project_folder_src, projects_folder)

        return ProjectFilePaths(project_token=token, paths=paths)

    finally:
        _cleanup(tmpfolder)


def _validate_project_structure(project_folder, token):
    project_folder_src = path.join(project_folder, token)

    has_src_folder = path.isdir(path.join(project_folder_src, "src"))
    has_data_folder = path.isdir(path.join(project_folder_src, "data"))

    error_messages = []
    if not has_src_folder:
        error_messages.append("missing a src folder")
    if not has_data_folder:
        error_messages.append("missing a data folder")

    if error_messages:
        error_message = "Project archive is " + " and ".join(error_messages)
        raise PackratException(error_message)


def _get_and_add_paths(project, token, project_folder):
    project_folder_src = path.join(project_folder, token)
    paths = _extract_files(project_folder_src)
    return project_folder_src, paths


def _extract_files(folder):
    fnames_list = []
    for (parent_dir, dirnames, fnames) in os.walk(folder):
        for fname in fnames:
            file_path = path.relpath(
                path.join(parent_dir, fname),
                folder)
            fnames_list.append(file_path)
    return fnames_list


def _cleanup(tmpfolder):
    if path.isdir(tmpfolder):
        shutil.rmtree(tmpfolder)


def _unpack(archive, folder):
    """
    Extract archive into tmpdir

    Extraction into a temporary directory is necessary in case an archive is submitted
    with multiple files and/or directories in the root

    :param archive:
    :type archive: str
    :param folder: folder to extract archive into
    :type folder: str
    """
    archive_dir, archive_name = path.split(archive)
    if not archive_dir:
        archive_dir = "."
    with utils.Chdir(archive_dir):
        pyunpack.Archive(archive_name).extractall(folder)


def _move_project_to_projects(folder, projects_folder):
    token = path.basename(folder)
    dest = path.join(path.expanduser(projects_folder), token)
    shutil.move(folder, dest)
    return dest
