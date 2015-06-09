from autoslug import AutoSlugField
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from model_utils import Choices

import logging
import os

logger = logging.getLogger(__name__)


class PostgresJSONField(models.TextField):

    description = "PostgreSQL JSON Field"

    def __init__(self, *args, **kwargs):
        kwargs.update(null=True, blank=True)
        super(PostgresJSONField, self).__init__(*args, **kwargs)

    # FIXME: consider performing Python <-> JSON magic conversions. see
    # https://docs.djangoproject.com/en/1.8/howto/custom-model-fields/ for more details

    def db_type(self, connection):
        return 'json'


class MiracleMetadataMixin(models.Model):
    """
    Provides commonly used metadata fields for Miracle metadata
    """
    name = models.CharField(max_length=255, default=None)
    full_name = models.CharField(max_length=512, blank=True)
    description = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    deleted_on = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, related_name="%(app_label)s_%(class)s_deleted_by_set", null=True, blank=True)
    creator = models.ForeignKey(User, related_name="%(app_label)s_%(class)s_creator_set")

    def clean(self):
        if not self.name:
            raise ValidationError("Please enter a project name")

    class Meta:
        abstract = True


class Project(MiracleMetadataMixin):

    slug = AutoSlugField(populate_from='name', unique=True)


class ProjectProvenanceMixin(models.Model):

    project = models.ForeignKey(Project, related_name="%(app_label)s_%(class)s_project_set")
    provenance = PostgresJSONField(blank=True)

    class Meta:
        abstract = True


class Author(models.Model):

    user = models.OneToOneField(User)
# FIXME: what is this for? arbitrary profile fields?
    attributes = PostgresJSONField(blank=True)


class Analysis(ProjectProvenanceMixin):

    data_path = models.TextField(blank=True, help_text=_("What is this for?"))
    authors = models.ManyToManyField(Author)


class Dataset(MiracleMetadataMixin, ProjectProvenanceMixin):

    slug = AutoSlugField(populate_from='name', unique=True)
    authors = models.ManyToManyField(Author)
    analyses = models.ManyToManyField(Analysis)


class DataTable(MiracleMetadataMixin):

    dataset = models.ForeignKey(Dataset)
    url = models.URLField(blank=True)

    @property
    def is_remote(self):
        return self.url is not None

    def generate_local_path(self):
        return os.path.join(self.dataset.path, self.pk)

    @property
    def path(self):
        return self.url or self.generate_local_path()


class DataTableColumn(models.Model):

    # FIXME: revisit + refine these data types
    ColumnDataType = Choices('int', 'bool', 'float', 'text')

    table = models.ForeignKey(DataTable, related_name='columns')
    name = models.CharField(max_length=64)
    display_name = models.CharField(max_length=128)
    description = models.TextField()
    data_type = models.CharField(max_length=128, choices=ColumnDataType, default=ColumnDataType.text)
