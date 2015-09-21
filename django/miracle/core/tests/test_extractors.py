import os, shutil
from django.conf import settings
#
from django.test import TestCase
from ..models import (User, Project)
from ..extractors import to_project_from_file, Extractor

# Enable if have project to test on in MIRACLE_TMP_DIRECTORY

# class ExtractorsTest(TestCase):
# 
#     @classmethod
#     def setUpTestData(cls):
#         cls.user = User.objects.create(username="miracle_user",
#                                        email="a@b.com",
#                                        password="aloha")
# 
#     def test_load_luxe(self):
#         project_path = os.path.join(settings.MIRACLE_TMP_DIRECTORY, "luxe.7z")
#         extractor = Extractor.from_archive(project_path)
#         metadata = extractor.metadata
#         groups = os.path.join(settings.MIRACLE_TMP_DIRECTORY, "luxe.miracle.yml")
#         project = to_project_from_file(metadata, groups, self.user)
#         self.assertEquals(u'Example1',
#                           project.analyses.first().name)
#         self.assertEquals(u'trans_2011_11_24_11_33_06_346',
#                           project.datasets.first().name)
# 
#     def test_load_did_ut_rhea(self):
#         project_path = os.path.join(settings.MIRACLE_TMP_DIRECTORY, "DID_UT_RHEA_v2.zip")
#         extractor = Extractor.from_archive(project_path)
#         metadata = extractor.metadata
#         groups = os.path.join(settings.MIRACLE_TMP_DIRECTORY, "DID_UT_RHEA_v2.miracle.yml")
#         project = to_project_from_file(metadata, groups, self.user)
#         self.assertEquals(u'ut_did',
#                           project.analyses.first().name)
