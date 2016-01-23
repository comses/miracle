import os
import mock
import requests

from .common import BaseMiracleTest
from ..ingest.loader import load_analyses, load_datatablegroup, load_deployr
from ..ingest.grouper import MetadataProject, MetadataAnalysis, MetadataDataTableGroup, MetadataDataFile
from ..models import DataAnalysisScript, DataTableGroup
from .. import utils

class MetadataGroupLoadersTest(BaseMiracleTest):
    TEST_PROJECT_DIRECTORY = os.path.join(os.getcwd(),
                                          "miracle", "core", "tests", "projects",
                                          "skeleton", "test")

    @property
    def default_analyses(self):
        a1 = MetadataAnalysis(name="a", path="src/a.R", parameters=[])
        a2 = MetadataAnalysis(name="b", path="src/b.R", parameters=[])
        a3 = MetadataAnalysis(name="c", path="src/c.R", parameters=[])

        return [a1, a2, a3]

    @property
    def default_datatablegroups(self):
        d1 = MetadataDataFile(name="a", path="data/a.csv")
        d2 = MetadataDataFile(name="a", path="data/a.shp")
        d3 = MetadataDataFile(name="b", path="data/b.shp")

        dg1 = MetadataDataTableGroup(name="datagroup a", properties=((None, "String"), (None, "Real")), datafiles=[d1])
        dg2 = MetadataDataTableGroup(name="datagroup b", properties=((None, "Real"), (None, "Date")),
                                     datafiles=[d2, d3])

        return [dg1, dg2]

    def grouped_metadata(self):
        project = self.create_project(name="test")
        return (project, MetadataProject(project_token=project.name,
                                         datatablegroups=self.default_datatablegroups,
                                         analyses=self.default_analyses))

    def test_load_analyses(self):
        project, grouped_metadata = self.grouped_metadata()
        load_analyses(self.default_analyses, project)

        a_analysis = DataAnalysisScript.objects.filter(name="a").first()
        self.assertEqual(a_analysis.archived_file, "src/a.R")

    def test_load_datatablegroups(self):
        project, grouped_metadata = self.grouped_metadata()

        load_datatablegroup(grouped_metadata.datatablegroups[0], project)

        a_datatablegroup = DataTableGroup.objects.filter(name="datagroup a").first()
        self.assertEquals(len(a_datatablegroup.columns.filter(name="", data_type="String")), 1)

    @mock.patch('miracle.core.ingest.loader.login')
    @mock.patch('miracle.core.ingest.loader.DeployrAPI.upload_script')
    @mock.patch('miracle.core.ingest.loader.DeployrAPI.create_working_directory')
    def test_load_deployr(self, cwd, upload_script, login):
        post_result_mock = mock.Mock()
        post_result_mock.status_code = 200
        cwd.return_value = post_result_mock
        upload_script.return_value = post_result_mock

        login_result_mock = mock.MagicMock(spec=requests.Session)
        login.return_value = login_result_mock

        project, grouped_metadata = self.grouped_metadata()
        metadata_analysis = MetadataAnalysis(name="init",
                                             path="src/init.R",
                                             parameters=self.default_analysisscript_params)
        with utils.Chdir(os.path.join(self.TEST_PROJECT_DIRECTORY, "test")):
            load_deployr([metadata_analysis], project)
