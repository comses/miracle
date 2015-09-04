import os
import pyunpack
from os import path
import shutil
import collections

from django.conf import settings
from .metadata import load_metadata, AnalysisMetadata


class MetaDataImportError(Exception):
    pass


def fileext_gen(file_names):
    for file_name in file_names:
        yield os.path.splitext(file_name)


class SHPFileGlob(object):
    """
    Shapefiles should be thought of as one unit

    e.g. A shapefile is composed of at least 4 files:
     a .shp, a .dbf, a .prj and a .shx
    """
    REQUIRED_EXTENSIONS = {".shp", ".dbf", ".prj", ".shx"}

    @staticmethod
    def from_files(file_names, log):

        shp_names = []
        for name, ext in fileext_gen(file_names):
            if ext == ".shp":
                shp_names.append(name)

        shp_file_groups = collections.defaultdict(set)
        for name, ext in fileext_gen(file_names):
            if name in shp_names:
                shp_file_groups[name].add(ext)

        names = []
        for shp_name in shp_names:
            if SHPFileGlob.is_valid(shp_file_groups[shp_name]):
                names.append(shp_name + ".shp")
            else:
                log.append("Shapefile is missing extensions {0} (only has {1})".
                           format(shp_name, SHPFileGlob.REQUIRED_EXTENSIONS.difference(shp_file_groups[shp_name])))

            for ext in shp_file_groups[shp_name]:
                file_names.remove(shp_name + ext)

        return names

    @staticmethod
    def is_valid(extensions):
        return extensions.issuperset(SHPFileGlob.REQUIRED_EXTENSIONS)


class OtherFileGlob(object):
    @staticmethod
    def from_files(file_names, log):
        return file_names


class FileGlobber(object):
    """
    Groups files that belong together and returns AnalysisMetadata
    """
    @staticmethod
    def extract_metadata(analysis_path):
        walker = os.walk(analysis_path)

        metadata = []
        log = []
        for root, dirs, files in walker:
            files = [f for f in files if not f[0] == '.']
            dirs[:] = [d for d in dirs if not d[0] == '.']
            shp_files = SHPFileGlob.from_files(files, log)
            other_files = OtherFileGlob.from_files(files, log)

            all_file_paths = other_files + shp_files
            for rel_file_path in all_file_paths:
                fullpath = path.join(root, rel_file_path)
                metadata.append(load_metadata(fullpath))

        return AnalysisMetadata(metadata, log)


class Extractor(object):
    """
    Create one extractor per uploaded analysis
    """
    ARCHIVE_FORMATS = [".7z", ".zip"]

    def __init__(self, analysis_name, analysis_path):
        self.analysis_path = analysis_path
        self.analysis_name = analysis_name

    @staticmethod
    def from_archive(fullpath, analysis_name):
        """
        Extracts an archive to a new folder

        :param fullpath: absolute path to where the analysis archive was
                         uploaded
        :param analysis_name: name of folder to name the analysis as
        :return: path to extracted analysis
        :raises: ValueError: unsupported archive format
        :raises: NameError: analysis_name already exists
        """
        directory, filename_ext = path.split(fullpath)
        filename, ext = path.splitext(filename_ext)
        if ext not in Extractor.ARCHIVE_FORMATS:
            raise ValueError("{} format not supported".format(ext))

        analysis_path = os.path.join(settings.MIRACLE_ANALYSIS_DIRECTORY, analysis_name)

        if not path.exists(analysis_path):
            pyunpack.Archive(fullpath).extractall(analysis_path, auto_create_dir=True)
        else:
            raise NameError("'{}' already exists. Try a different name.".format(analysis_name))

        Extractor._cleanup(analysis_name)
        return Extractor(analysis_name, analysis_path)

    @staticmethod
    def _cleanup(analysis_name):
        """
        Move all analysis files up one directory, if only one subdirectory
        """
        analysis_path = path.join(settings.MIRACLE_ANALYSIS_DIRECTORY, analysis_name)
        dirs = os.listdir(analysis_path)
        if "__MACOSX" in dirs:
            dirs.remove("__MACOSX")
        if len(dirs) == 1:
            directory = dirs[0]
            files = os.listdir(path.join(analysis_path, directory))

            for file in files:
                shutil.move(path.join(analysis_path, directory, file),
                            path.join(analysis_path, file))

            os.rmdir(path.join(analysis_path, directory))

    def extract_metadata(self):
        """
        Create metadata from the extracted archive

        :return: metadata for the analysis and all its datasets
        :rtype: AnalysisMetadata
        """
        analysis_metadata = FileGlobber.extract_metadata(self.analysis_path)
        return analysis_metadata
