from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


class PostgresJSONField(models.TextField):

    description = "PostgreSQL JSON Field"

    # FIXME: consider performing Python <-> JSON magic conversions. see
    # https://docs.djangoproject.com/en/1.8/howto/custom-model-fields/ for more details

    def db_type(self, connection):
        return 'json'


class MiracleMetadataMixin(models.Model):
    """
    Provides commonly used metadata fields for Miracle metadata
    """
    short_name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=512, blank=True)
    description = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    deleted_on = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, related_name="%(app_label)s_%(class)s_deleted_by_set")
    creator = models.ForeignKey(User, related_name="%(app_label)s_%(class)s_creator_set")

    class Meta:
        abstract = True


class Project(MiracleMetadataMixin):
    slug = models.SlugField()


class ProjectProvenanceMixin(models.Model):

    project = models.ForeignKey(Project, related_name="%(app_label)s_%(class)s_project_set")
    provenance = PostgresJSONField(blank=True)

    class Meta:
        abstract = True


class Author(models.Model):

    user = models.OneToOneField(User)
# FIXME: what is this for?
    attributes = PostgresJSONField(blank=True)


class Analysis(ProjectProvenanceMixin):

    data_path = models.TextField(blank=True, help_text=_("What is this for?"))
    authors = models.ManyToManyField(Author)


class Dataset(MiracleMetadataMixin, ProjectProvenanceMixin):

    authors = models.ManyToManyField(Author)
    analyses = models.ManyToManyField(Analysis)
