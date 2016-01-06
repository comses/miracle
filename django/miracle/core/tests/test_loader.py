from .common import BaseMiracleTest
from ..ingest.loader import load_datatablegroupfiles, load_analyses, load_datatablegroup
from ..ingest.grouper import MetadataProject, MetadataAnalysis, MetadataDataTableGroup, MetadataDataTable
from ..models import DataAnalysisScript, DataTableGroup


class MetadataGroupLoadersTest(BaseMiracleTest):
    @property
    def default_analyses(self):
        a1 = MetadataAnalysis(name="a", path="src/a.R")
        a2 = MetadataAnalysis(name="b", path="src/b.R")
        a3 = MetadataAnalysis(name="c", path="src/c.R")

        return [a1, a2, a3]

    @property
    def default_datatablegroups(self):
        d1 = MetadataDataTable(name="a", path_ids=(0,))
        d2 = MetadataDataTable(name="a", path_ids=(1, 2))
        d3 = MetadataDataTable(name="b", path_ids=(3, 4))

        dg1 = MetadataDataTableGroup(name="datagroup a", properties=((None, "String"), (None, "Real")), datatables=[d1])
        dg2 = MetadataDataTableGroup(name="datagroup b", properties=((None, "Real"), (None, "Date")),
                                     datatables=[d2, d3])

        return [dg1, dg2]

    @property
    def default_paths(self):
        return ["data/a.csv", "data/a.shp", "data/a.dbf", "data/b.shp", "data/b/dbf",
                "src/a.R", "src/b.R", "src/c.R", "README.md"]

    def grouped_metadata(self):
        project = self.create_project(name="test")
        return (project, MetadataProject(project_token=project.name,
                                         datatablegroups=self.default_datatablegroups,
                                         analyses=self.default_analyses,
                                         paths=self.default_paths))

    def test_load_datasetfiles(self):
        project, grouped_metadata = self.grouped_metadata()
        datasetfiles = load_datatablegroupfiles(grouped_metadata, project)

        self.assertEqual(datasetfiles[8].archived_file, "README.md")

    def test_load_analyses(self):
        project, grouped_metadata = self.grouped_metadata()
        load_analyses(self.default_analyses, project)

        a_analysis = DataAnalysisScript.objects.filter(name="a").first()
        self.assertEqual(a_analysis.archived_file, "src/a.R")

    def test_load_datatablegroups(self):
        project, grouped_metadata = self.grouped_metadata()
        datasetfiles = load_datatablegroupfiles(grouped_metadata, project)

        load_datatablegroup(grouped_metadata.datatablegroups[0], project, datasetfiles)

        a_datatablegroup = DataTableGroup.objects.filter(name="datagroup a").first()
        self.assertEquals(len(a_datatablegroup.columns.filter(name="", data_type="String")), 1)
