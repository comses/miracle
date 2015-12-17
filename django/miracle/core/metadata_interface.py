import shutil
import logging

from django.conf import settings
from os import path

from .models import Project

logger = logging.getLogger(__name__)

def delete_project(project, projects_folder = settings.MIRACLE_PROJECT_DIRECTORY):
    """
    Completely delete a project  (files and in the database)

    :param project: Project you want to delete
    :type project: Project
    :param projects_folder: location of the projects folder
    :return:
    """
    # TODO: move this inot the Project model
    try:
        project_folder = path.join(projects_folder, project.path)
        shutil.rmtree(project_folder)
    except Exception, e:
        logger.error("delete_project: '{}', chould not remove path {}".format(e, project.path))
    project.delete()
