import os
import shutil

from .unarchiver import extract
from .analyzer import group_files
from .grouper import group_metadata
from .loader import load_project


def run(project, archive):
    try:
        project_file_paths = extract(project, archive)
        project_grouped_file_paths = group_files(project_file_paths)
        metadata_project = group_metadata(project_grouped_file_paths)
        load_project(metadata_project)
    except Exception:
        cleanup_on_error(project)
        raise


def cleanup_on_error(project):
    archive_path = project.archive_path
    project_path = project.project_path
    packrat_path = project.packrat_path

    if os.path.exists(archive_path):
        os.unlink(archive_path)
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
    if os.path.exists(packrat_path):
        shutil.rmtree(packrat_path)