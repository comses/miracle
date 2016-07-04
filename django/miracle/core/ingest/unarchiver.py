from os import path
import os
import shutil
import pyunpack
from ...core import utils
import tempfile
import logging

from django.conf import settings

from . import ProjectFilePaths, PackratException, ProjectDirectoryAlreadyExists
from ..models import Project

logger = logging.getLogger(__name__)

def extract(project, archive):
    """
    Extract a project archive into the project folder

    :param project: a project to associate the archive with
    :type project: miracle.core.models.Project
    :param archive: a path to an archive file
    :type archive: str

    :return: a ProjectFilePaths object with the project token and the project path db records
    :rtype: ProjectFilePaths
    """

    projects_folder = settings.PROJECT_DIRECTORY
    packrat_folder =  settings.PACKRAT_DIRECTORY

    tmpfolder = tempfile.mkdtemp()
    token = project.slug
    _check_already_exists(projects_folder, token)
    _check_already_exists(packrat_folder, token)

    try:
        _unpack(archive, tmpfolder)

        files = os.listdir(tmpfolder)
        if len(files) != 1:
            raise PackratException("root folder is not unique. contains {}".format(files.__str__()))

        project_folder = path.join(tmpfolder, files[0])
        if not path.isdir(project_folder):
            raise PackratException("root {} is not a folder".format(projects_folder))

        project_folder_contents = os.listdir(project_folder)
        logger.debug("project folder contents: %s", project_folder_contents)
        if "packrat" not in project_folder_contents:
            raise PackratException("no Packrat folder")
        if token not in project_folder_contents:
            raise PackratException("no project folder named {} exists".format(token))

        _validate_project_structure(project_folder, token)
        project_folder_src, paths = _get_and_add_paths(project, token, project_folder)
        _move_project_to_projects(project_folder_src, projects_folder)
        _move_packrat_to_packrats(project_folder_src, settings.PACKRAT_DIRECTORY)

        return ProjectFilePaths(project_token=token, paths=paths)

    finally:
        _cleanup(tmpfolder)


def _check_already_exists(folder, slug):
    full_path = os.path.join(folder, slug)
    if os.path.exists(full_path):
        error = ProjectDirectoryAlreadyExists("PATH ALREADY EXISTS: %s" % full_path)
        logger.exception(error)
        raise error


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
        try:
            pyunpack.Archive(archive_name).extractall(folder)
        except ValueError as e:
            logging.exception(e)
            raise OSError(e)

def _move_project_to_projects(folder, projects_folder):
    token = path.basename(folder)
    dest = path.join(path.expanduser(projects_folder), token)
    shutil.move(folder, dest)
    return dest

def _move_packrat_to_packrats(folder, packrats_folder):
    parent_folder, token = path.split(folder)
    src = path.join(parent_folder, 'packrat')
    dest = path.join(path.expanduser(packrats_folder), token)
    shutil.move(src, dest)
    return dest
