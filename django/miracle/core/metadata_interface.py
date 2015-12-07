from django.conf import settings

from .extractors import Packrat, MetadataFileExtractor
from models import Project
import shutil
from os import path

import logging

logger = logging.getLogger(__name__)

def add_project(project, archive, projects_folder = settings.MIRACLE_PROJECT_DIRECTORY):
    """
    Extract and associate an archive with a project.
    Also insert file path information into the database

    :param archive: path to archive
    :type Archive: str
    :param project: project database record
    :type project: Project
    :return:
    """
    packrat = Packrat.extract(project, archive, projects_folder)
    packrat.cleanup()
    return packrat

def delete_project(project, projects_folder = settings.MIRACLE_PROJECT_DIRECTORY):
    """
    Completely delete a project  (files and in the database)

    :param project: Project you want to delete
    :type project: Project
    :param projects_folder: location of the projects folder
    :return:
    """
    try:
        project_folder = path.join(projects_folder, project.path)
        shutil.rmtree(project_folder)
    except Exception, e:
        logger.error("delete_project: '{}', chould not remove path {}".format(e, project.path))
    project.delete()

def associate_metadata_with_file(projectpath):
    """
    Extract metadata from path

    :param projectpath: ProjectPath
    :return:
    """
    return MetadataFileExtractor.extract_file_metadata(projectpath)