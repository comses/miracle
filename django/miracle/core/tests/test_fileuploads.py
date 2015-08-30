
from ..fileuploads import process_uploaded_analysis, process_uploaded_dataset
from ..models import Analysis
from django.conf import settings
from os import path
import os

from .common import BaseMiracleTest


class FileUploadsTest(BaseMiracleTest):
    ANALYSIS_PATH = path.join(settings.BASE_DIR, 'miracle', 'core', 'tests', 'analyses')

    def test_analysis_upload(self):
        process_uploaded_analysis(path.join(self.ANALYSIS_PATH, "r_example.7z"),
                                            self.default_project,
                                            self.default_user)
        datasets = Analysis.objects.get(name="r_example.7z").dataset_set.all()
        dataset_names = {dataset.name for dataset in datasets}
        self.assertEquals(dataset_names,
                          {"README.md", "README.md~", "cars.csv", "transform.R","src.Rproj", "test.svg"})

    def test_headless_csv_upload(self):
        analysis = self.default_analysis
        os.makedirs(path.join(self.MIRACLE_ANALYSIS_DIR, str(analysis.id)))
        process_uploaded_dataset(self.get_test_data("headless.csv"),
                                 analysis,
                                 self.default_project,
                                 self.default_user, copy=True)
        datasets = analysis.dataset_set.all()
        dataset_names = {dataset.name for dataset in datasets}
        self.assertEquals(dataset_names, {"headless.csv"})
