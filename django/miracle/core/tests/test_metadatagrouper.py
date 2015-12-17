from .common import BaseMiracleTest
from ..filegrouper import ShapefileFileGroup, OtherFile
from ..filegroup_extractors import MetadataCollection, Metadata, DataTypes, MetadataFileGroup
from ..metadatagrouper import MetadataDataTableGroup, to_datatablegroups, group_metadata

class MetadataGrouperTest(BaseMiracleTest):

    def metadata(self):
        file_paths = ["data/a.shp", "data/a.dbf", "data/b.shp", "data/b.dbf", "data/a.txt", "data/b.csv",
                      "src/test.R"]

        g1 = ShapefileFileGroup(file_paths=file_paths[0:1],inds=(0,1))
        m1 = Metadata("data/a.shp",DataTypes.data, {}, [(None, (("a", "Real"), ("d", "String")))])
        gm1 = MetadataFileGroup(group=g1, metadata=m1)

        g2 = ShapefileFileGroup(file_paths=file_paths[2:3],inds=(2,3))
        m2 = Metadata("data/b.shp",DataTypes.data, {}, [(None, (("a", "Real"), ("d", "String")))])
        gm2 = MetadataFileGroup(group=g2, metadata=m2)

        g3 = OtherFile(file_path=file_paths[4], ind=4)
        m3 = Metadata("data/a.txt",DataTypes.data, {}, [(None, (("id", "Real"), ("count", "Real")))])
        gm3 = MetadataFileGroup(group=g3, metadata=m3)

        g4 = OtherFile(file_path=file_paths[5], ind=5)
        m4 = Metadata("data/b.csv",DataTypes.data, {}, [(None, ((None, "Real"), (None, "Date")))])
        gm4 = MetadataFileGroup(group=g4, metadata=m4)

        g5 = OtherFile(file_path=file_paths[6], ind=6)
        m5 = Metadata("src/test.R",DataTypes.code, {}, [])
        gm5 = MetadataFileGroup(group=g5, metadata=m5)

        project_token = "test"

        return MetadataCollection(project_token=project_token,
                                  metadata_file_groups=[gm1, gm2, gm3, gm4, gm5],
                                  paths=file_paths)

    def test_metadata_grouping(self):
        """
        Convert the metadata into datatablegroups where the metadata objects have the same layers
        """
        metadata = self.metadata()
        column_metadata = {}
        datatablegroups = []

        for i in xrange(4):
            to_datatablegroups(metadata.metadata_file_groups[i], column_metadata, datatablegroups)

        column_sets = column_metadata.keys()
        self.assertIn((("a", "Real"), ("d", "String")), column_sets)
        self.assertIn((("id", "Real"), ("count", "Real")), column_sets)
        self.assertEqual(len(column_sets), 2)
        self.assertEqual(len(datatablegroups), 1)
