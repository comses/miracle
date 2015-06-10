from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, connections
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import AutoSlugField

from model_utils import Choices
from model_utils.managers import PassThroughManager

import logging
import os
import re

logger = logging.getLogger(__name__)


class PostgresJSONField(models.TextField):

    description = "PostgreSQL JSON Field"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)
        super(PostgresJSONField, self).__init__(*args, **kwargs)

    # FIXME: consider performing Python <-> JSON magic conversions. see
    # https://docs.djangoproject.com/en/1.8/howto/custom-model-fields/ for more details

    def db_type(self, connection):
        return 'json'


class DatasetConnectionMixin(object):

    MAX_NAME_LENGTH = 63
    connection = connections['datasets']

    def _is_valid_identifier(self, value, prefix='m'):
        regex = r'^' + prefix + '\d+\w+$'
        return len(value) <= 63 and re.match(regex, value)

    def sanitize_name(self, name):
        if not self._is_valid_identifier(name):
            original_name = name
            self.name = self.sanitize_identifier(original_name)
            if not self.full_name:
                self.full_name = original_name
            self.save()

    def sanitize_identifier(self, name, prefix='m'):
        """
        Returns a normalized string that can be used as a valid Postgres identifier (e.g., table or column name), see
        http://www.postgresql.org/docs/9.4/static/sql-syntax-lexical.html#SQL-SYNTAX-IDENTIFIERS

        Assumes that this entity has already been assigned a PK and is persistent in the database.
        """
        if not name:
            name = 'blank'
        # convert to lowercase, replace all non-alphabetic characters with underscore and truncate repeated non-word
        # characters into a single underscore
        sanitized_name = re.sub('[^\w]+', '_', name.lower())
        # ensure leading character is alphabetic and append pk for relative uniqueness across DataTables and
        # DataTableColumns (i.e., DataTable names must be unique across all DataTables, DataTableColumn names must be
        # unique within the given DataTable).
        prefix += str(self.pk)
        if sanitized_name[0].isalpha():
            prefix = prefix + '_'
        sanitized_name = prefix + sanitized_name
        # identifier must be < NAMEDATALEN, (63 characters by default unless using custom compiled postgres)
        sanitized_name = sanitized_name[:self.MAX_NAME_LENGTH]
        logger.debug("sanitized name: %s", sanitized_name)
        return sanitized_name

    @property
    def cursor(self):
        return self.connection.cursor()


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

    def __unicode__(self):
        return u'{} (internal: {})'.format(self.full_name, self.name)

    class Meta:
        abstract = True


class Project(MiracleMetadataMixin):

    slug = AutoSlugField(populate_from='name', unique=True)

    @property
    def path(self):
        return os.path.join(settings.MIRACLE_DATA_DIRECTORY, 'project', self.pk)

    def get_absolute_url(self):
        return u"/project/{}".format(self.slug)


class Author(models.Model):

    user = models.OneToOneField(User)
    attributes = PostgresJSONField()


class Analysis(models.Model):

    project = models.ForeignKey(Project, related_name="analyses")
    provenance = PostgresJSONField()
    data_path = models.TextField(blank=True, help_text=_("What is this for?"))
    authors = models.ManyToManyField(Author)


class DatasetQuerySet(models.query.QuerySet):
    pass


class DatasetManager(PassThroughManager):

    use_for_related_fields = True

    def create(self, *args, **kwargs):
        project = kwargs.get('project', None)
        if project is None:
            raise ValidationError("Datasets must be associated with a Project")
        kwargs.setdefault('creator', project.creator)
        return super(DatasetManager, self).create(*args, **kwargs)


def _local_dataset_path(dataset, filename):
    return os.path.join(dataset.project.path, 'dataset', filename)


class Dataset(MiracleMetadataMixin):

    """
    Assumes one file per Dataset. A Dataset can consist of multiple DataTables, e.g., an Excel file with multiple sheets
    is a single Dataset with multiple DataTables, likewise an Access database.
    """

    slug = AutoSlugField(populate_from='name', unique=True)
    project = models.ForeignKey(Project, related_name="datasets")
    provenance = PostgresJSONField()
    authors = models.ManyToManyField(Author)
    analyses = models.ManyToManyField(Analysis)
    url = models.URLField(blank=True)
    datafile = models.FileField(upload_to=_local_dataset_path)

    objects = DatasetManager.for_queryset_class(DatasetQuerySet)()

    def get_absolute_url(self):
        return u"/dataset/{}".format(self.slug)


class DataTableQuerySet(models.query.QuerySet):
    pass


class DataTableManager(PassThroughManager):

    use_for_related_fields = True

    def create(self, *args, **kwargs):
        dataset = kwargs.get('dataset', None)
        if dataset is None:
            raise ValidationError("DataTables must be associated with a Dataset")
        kwargs.setdefault('creator', dataset.creator)
        return super(DataTableManager, self).create(*args, **kwargs)


class DataTable(MiracleMetadataMixin, DatasetConnectionMixin):

    """
    DataTable.name will be used for the internal RDBMS table name in the miracle_data database
    DataTable.full_name is the user assigned data table name (e.g., CSV filename, Excel sheet name, user supplied name)
    """

    dataset = models.ForeignKey(Dataset, related_name='tables')
    objects = DataTableManager.for_queryset_class(DataTableQuerySet)()

    @property
    def attributes(self):
        return {
            'column_a': 'bigint'
        }

    def select_all(self):
        cursor = self.cursor
        cursor.execute("SELECT * FROM {}".format(self.name))
        return cursor.fetchall()

    def create_schema(self):
        """
        Generates DDL and updates this model's name and full_name fields as well as its child columns.
        """
        self.sanitize_name(self.name)
        for c in self.columns.all():
            c.sanitize_name(c.name)
        create_table_statement = "CREATE TABLE {} ({})".format(self.name, self.attributes)
        logger.debug("create table statement: %s", create_table_statement)
        return create_table_statement


class DataTableColumn(models.Model, DatasetConnectionMixin):

    """
    Metadata for a Column in a given DataTable
    """
    # FIXME: revisit + refine these data types
    DataType = Choices(
        ('bigint', _('integer')),
        ('boolean', _('boolean')),
        ('decimal', _('floating point number')),  # worse performance than float but avoids rounding errors
        ('text', _('text')),
    )

    table = models.ForeignKey(DataTable, related_name='columns')
    name = models.CharField(max_length=64, default=None, help_text=_("Internal data table name"))
    full_name = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    data_type = models.CharField(max_length=128, choices=DataType, default=DataType.text)

    def all_values(self, distinct=False):
        ''' returns a list resulting from select name from data table using miracle_data database '''
        statement = "SELECT {} {} FROM {}".format('DISTINCT' if distinct else '', self.name, self.table.name)
        self.cursor.execute(statement)
        return self.cursor.fetchall()

    def __unicode__(self):
        return u'{} (internal: {})'.format(self.full_name, self.name)
