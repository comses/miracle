from .common import BaseMiracleTest
from ..ingest.analyzer import ShapefileFileGroup, OtherFile, Metadata, DataTypes
from ..ingest.grouper import MetadataDataTableGroup, to_datatablegroups, group_metadata
from ..ingest import ProjectGroupedFilePaths

class MetadataGrouperTest(BaseMiracleTest):

    def metadata(self):
        file_paths = ["data/a.shp", "data/a.dbf", "data/b.shp", "data/b.dbf", "data/a.txt", "data/b.csv",
                      "src/test.R"]

        m1 = Metadata("data/a.shp",DataTypes.data, {}, [(None, (("a", "Real"), ("d", "String")))])
        g1 = ShapefileFileGroup(file_paths=file_paths[0:1],inds=(0,1), metadata=m1)

        m2 = Metadata("data/b.shp",DataTypes.data, {}, [(None, (("a", "Real"), ("d", "String")))])
        g2 = ShapefileFileGroup(file_paths=file_paths[2:3],inds=(2,3), metadata=m2)

        m3 = Metadata("data/a.txt",DataTypes.data, {}, [(None, (("id", "Real"), ("count", "Real")))])
        g3 = OtherFile(file_path=file_paths[4], ind=4, metadata=m3)

        m4 = Metadata("data/b.csv",DataTypes.data, {}, [(None, ((None, "Real"), (None, "Date")))])
        g4 = OtherFile(file_path=file_paths[5], ind=5, metadata=m4)

        m5 = Metadata("src/test.R",DataTypes.code, {}, [])
        g5 = OtherFile(file_path=file_paths[6], ind=6, metadata=m5)

        project_token = "test"

        return ProjectGroupedFilePaths(project_token=project_token,
                                       grouped_paths=[g1, g2, g3, g4, g5],
                                       paths=file_paths)

    def test_metadata_grouping(self):
        """
        Convert the metadata into datatablegroups where the metadata objects have the same layers
        """
        metadata = self.metadata()
        column_metadata = {}
        datatablegroups = []

        for i in xrange(4):
            to_datatablegroups(metadata.grouped_paths[i], column_metadata, datatablegroups)

        column_sets = column_metadata.keys()
        self.assertIn((("a", "Real"), ("d", "String")), column_sets)
        self.assertIn((("id", "Real"), ("count", "Real")), column_sets)
        self.assertEqual(len(column_sets), 2)
        self.assertEqual(len(datatablegroups), 1)
