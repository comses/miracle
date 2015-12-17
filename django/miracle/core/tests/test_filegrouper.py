from ..filegrouper import group_files, ShapefileFileGroup, OtherFile, ProjectGroupedFilePaths
from ..archive_extractor import ProjectFilePaths
from .common import BaseMiracleTest


class FileGrouperTest(BaseMiracleTest):

    def projectfilepaths(self):
        return ProjectFilePaths(project_token='test',
                                paths=["data/a.shp", "data/a.dbf", "data/a.prj", "data/a.shx", "data/a.txt",
                                       "data/b.shp", "data/b.dbf", "data/b.prj"])

    def test_baseshapefilepaths(self):
        project_file_paths = self.projectfilepaths()
        project_grouped_file_paths = group_files(project_file_paths)

        self.assertIn(ShapefileFileGroup(["data/a.shp", "data/a.dbf", "data/a.prj", "data/a.shx"], (0,1,2,3)),
                      project_grouped_file_paths.grouped_paths)

        self.assertIn(ShapefileFileGroup(["data/b.shp", "data/b.dbf", "data/b.prj"], (5,6,7)),
                      project_grouped_file_paths.grouped_paths)

        self.assertIn(OtherFile("data/a.txt", 4),
                      project_grouped_file_paths.grouped_paths)

