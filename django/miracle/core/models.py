from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db import models, connections
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
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
            if not getattr(self, 'full_name', None):
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
    published_on = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(User, related_name="%(app_label)s_%(class)s_publisher_set", null=True, blank=True)
    deleted_on = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, related_name="%(app_label)s_%(class)s_deleted_by_set", null=True, blank=True)
    creator = models.ForeignKey(User, related_name="%(app_label)s_%(class)s_creator_set")

    @property
    def published(self):
        return self.published_on is not None

    @property
    def deleted(self):
        return self.deleted_on is not None

    @property
    def status(self):
        if self.deleted:
            return "Deleted"
        elif self.published:
            return "Published"
        else:
            return "Draft"

    def publish(self, user, defer=False):
        if not self.published_on:
            self.published_on = timezone.now()
            self.published_by = user
            if not defer:
                self.save()
            ActivityLog.objects.log_user(user, 'Published {} on {}'.format(unicode(self), self.published_on))

    def unpublish(self, user, defer=False):
        original_published_on = self.published_on
        if original_published_on:
            self.published_on = None
            self.published_by = None
            if not defer:
                self.save()
            ActivityLog.objects.log_user(
                user, 'Unpublished {}, originally published on {}'.format(unicode(self), original_published_on))

    def deactivate(self, user):
        if not self.deleted_on:
            self.deleted_on = timezone.now()
            self.deleted_by = user
            self.save()
            ActivityLog.objects.log_user(
                user, 'Deactivating {} on {}'.format(unicode(self), self.deleted_on))

    def activate(self, user):
        original_deleted_on = self.deleted_on
        if original_deleted_on:
            self.deleted_on = None
            self.deleted_by = None
            self.save()
            ActivityLog.objects.log_user(
                user, 'Reactivating {}, originally deactivated on {}'.format(unicode(self), original_deleted_on))

    def __unicode__(self):
        return u'{} (internal: {})'.format(self.full_name, self.name)

    class Meta(object):
        abstract = True


class ActivePublishedQuerySet(models.query.QuerySet):

    def active(self, *args, **kwargs):
        return self.filter(deleted_on__isnull=True, *args, **kwargs)

    def published(self, *args, **kwargs):
        return self.filter(published_on__isnull=False, *args, **kwargs)


class ProjectQuerySet(ActivePublishedQuerySet):

    def viewable(self, user, *args, **kwargs):
        """
        Projects are viewable when they:
        1. are active
        2. are published
        3. are created by the given user
        4. have the given user as a member of the project's group
        """
        if not user or not user.is_authenticated():
            return self.active().published()
        # FIXME: figure out why distinct() is necessary here
        return self.filter(models.Q(creator=user) | models.Q(group__user=user) |
                           (models.Q(deleted_on__isnull=True) & models.Q(published_on__isnull=False))).distinct()


class Project(MiracleMetadataMixin):

    slug = AutoSlugField(populate_from='name', unique=True)
    group = models.OneToOneField(Group, editable=False,
                                 help_text=_("Members of this group can edit this project's datasets and metadata"),
                                 null=True)
    objects = PassThroughManager.for_queryset_class(ProjectQuerySet)()

    @property
    def path(self):
        return os.path.join(settings.MIRACLE_DATA_DIRECTORY, 'project', str(self.slug))

    @property
    def uploads_path(self):
        return os.path.join(self.path, 'uploads')

    @property
    def group_name(self):
        ''' unique name to manage permissions for this project '''
        return u'{} Group #{}'.format(self.name, self.pk)

    @property
    def group_members(self):
        return self.group.user_set.values_list('username', flat=True)

    def has_group_member(self, user):
        return self.creator == user or user.groups.filter(name=self.group_name).exists()

    def add_group_member(self, user):
        return user.groups.add(self.group)

    def set_group_members(self, users):
        self.group.user_set = users

    def remove_group_member(self, user):
        return user.groups.remove(self.group)

    def bookmark_for(self, user):
        bookmarked_project, created = BookmarkedProject.objects.get_or_create(project=self, user=user)
        return bookmarked_project

    @property
    def number_of_datasets(self):
        return self.datasets.count()

    @property
    def outputs(self):
        return AnalysisOutput.objects.filter(analysis__project=self)

    def get_absolute_url(self):
        return reverse_lazy('core:project-detail', args=[self.pk])

    class Meta(object):
        permissions = (
            ('view_project', 'Can view this project'),
            ('edit_project', 'Can edit this project'),
            ('admin_project', 'Full admin over this project'),
            ('create_projects', 'Can create projects'),
        )


@receiver(post_save, sender=Project)
def project_group_creator(sender, instance, created, raw, using, update_fields, **kwargs):
    if created:
        group, created = Group.objects.get_or_create(name=instance.group_name)
        group.user_set.add(instance.creator)
        instance.group = group
        instance.save()
    else:
        assert instance.group is not None


class BookmarkedProject(models.Model):

    project = models.ForeignKey(Project)
    user = models.ForeignKey(User, related_name='bookmarked_projects')

    class Meta:
        unique_together = ('project', 'user')


class Author(models.Model):

    user = models.OneToOneField(User)
    attributes = PostgresJSONField()

    def __unicode__(self):
        return self.user.email


def _local_analysis_path(analysis, filename):
    return os.path.join(analysis.project.upload_path, 'scripts', filename)


class Analysis(MiracleMetadataMixin):
    # FIXME: rename to Script/ScriptParameter/ScriptOutput? Consider after the demo.

    FileType = Choices(
        ('R', _('R script')),
        ('Julia', _('Julia script')),
        ('Python', _('Python script')),
        ('Perl', _('Perl script')),
    )

    slug = AutoSlugField(populate_from='name', unique=True)
    project = models.ForeignKey(Project, related_name="analyses")
    provenance = PostgresJSONField()
    parameters_json = PostgresJSONField(help_text=_("Supported input parameters in JSON format for this analysis script"))
    uploaded_file = models.FileField(upload_to=_local_analysis_path)
    archived_file = models.FileField(blank=True, help_text=_("Archived script file to be run in a sandbox."))
    file_type = models.CharField(max_length=128, choices=FileType, default=FileType.R)
    authors = models.ManyToManyField(Author)

    @property
    def input_parameters(self):
# returns a list of dicts for easier JSON consumption
        return [dict(name=k, **v) for k, v in self.get_deployr_parameters_dict().items()]


    def get_deployr_parameters_dict(self, values=None):
        if values is None:
            values = {}
        return dict(
            (p.name, {'label': p.label, 'type': 'primitive', 'rclass': p.data_type, 'value': values.get(p.name, p.default_value)})
            for p in self.parameters.all()
        )

    def __unicode__(self):
        return u'{} {}'.format(self.name, self.uploaded_file.url)


class AnalysisParameter(models.Model):

    # XXX: currently 1:1 with R data types, support for other types of analysis scripts require additional mappings
    ParameterType = Choices(
        ('integer', _('integer')),
        ('logical', _('boolean')),
        ('numeric', _('floating point number')),
        ('character', _('character')),
        ('complex', _('complex numbers')),
    )

    TYPE_CONVERTERS = {
        'integer': int,
        'logical': bool,
        'numeric': float,
        'character': str,
        'complex': complex,
    }

    analysis = models.ForeignKey(Analysis, related_name='parameters')
    name = models.CharField(max_length=255, help_text=_("Input parameter variable name used in this analysis script."))
    label = models.CharField(max_length=255, help_text=_("Human-friendly label for this parameter."), blank=True)
    description = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    data_type = models.CharField(max_length=128, choices=ParameterType, default=ParameterType.character)
    default_value = models.CharField(max_length=255, blank=True,
                                     help_text=_("default value for this analysis input parameter"))

    def convert(self, value):
        return TYPE_CONVERTERS[self.data_type](value)

    def __unicode__(self):
        return u'{} ({})'.format(self.label, self.name)


class AnalysisOutput(models.Model):

    analysis = models.ForeignKey(Analysis, related_name='outputs')
    name = models.CharField(max_length=255, help_text=_("User assigned name for this script run"))
    description = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(User)
    parameter_values_json = PostgresJSONField(help_text=_("Input parameter values used in the given analysis run"))
    response = PostgresJSONField(help_text=_("Internal raw HTTP response from executing the script against DeployR/OpenCPU"))

    def __unicode__(self):
        return u'[{}] output from running {} on {} by {} with parameters {}'.format(
            self.name, self.analysis, self.date_created, self.creator, self.parameter_values_json
        )


class ParameterValue(models.Model):

    parameter = models.ForeignKey(AnalysisParameter)
    output = models.ForeignKey(AnalysisOutput, related_name='parameter_values')
    value = models.CharField(max_length=255, help_text=_("Assigned value for the given input parameter"))


def _analysis_output_path(instance, filename):
    return os.path.join(settings.OUTPUT_FILE_PATH, self.project_slug)


class AnalysisOutputFile(models.Model):

    output = models.ForeignKey(AnalysisOutput, related_name='files')
    output_file = models.FilePathField(path=_analysis_output_path)

    @property
    def project_slug(self):
        return self.output.analysis.project.slug


class DatasetQuerySet(models.query.QuerySet):

    def viewable(self, user, *args, **kwargs):
        """
        Datasets are viewable when they:
        1. are active
        2. are published
        3. are created by the given user
        4. have the given user as a member of their parent project's group
        """
        if not user or not user.is_authenticated():
            return self.active().published()
        return self.filter(models.Q(creator=user) |
                           models.Q(project__group__user=user) |
                           (models.Q(deleted_on__isnull=True) & models.Q(published_on__isnull=False))).distinct('id')


class DatasetManager(PassThroughManager):

    use_for_related_fields = True

    def create(self, *args, **kwargs):
        project = kwargs.get('project', None)
        if project is None:
            raise ValidationError("Datasets must be associated with a Project")
        kwargs.setdefault('creator', project.creator)
        return super(DatasetManager, self).create(*args, **kwargs)


def _local_dataset_path(dataset, filename):
    return os.path.join(dataset.uploads_path, filename)


def _local_datatable_path(datatable, filename):
    return os.path.join(datatable.dataset.uploads_path, 'datatables', filename)


class Dataset(MiracleMetadataMixin):
    """
    A Dataset maintains a schema + metadata for its associated DataTables. For example, an Excel file with N sheets
    where each sheet has a different schema would be represented as N Datasets with single DataTables. Likewise,
    a directory with 600 data files that all share the same schema would be represented as a single Dataset with 600
    DataTables. A Dataset always has at least one DataTable, and a DataTable corresponds to a single file.

    Although we aren't promising to be a digital preservation repository we should still loosely hold the concepts of
    Submission Information Packages, Archival Information Packages, and Dissemination Information Packages as defined by
    the OAIS reference model (http://www2.archivists.org/groups/standards-committee/open-archival-information-system-oais)
    """

    slug = AutoSlugField(populate_from='name', unique=True)
    project = models.ForeignKey(Project, related_name="datasets")
    provenance = PostgresJSONField()
    authors = models.ManyToManyField(Author)
    analyses = models.ManyToManyField(Analysis)
    uploaded_file = models.FileField(upload_to=_local_dataset_path, help_text=_("The original uploaded dataset file (loosely corresponding to a SIP)"))
    data_type = models.CharField(max_length=50, blank=True)
    properties = PostgresJSONField(help_text=_("Schema and metadata for this Dataset, applicable to all child DataTables"))
    external_url = models.URLField(blank=True)

    objects = DatasetManager.for_queryset_class(DatasetQuerySet)()

    @property
    def uploads_path(self):
        return os.path.join(self.project.uploads_path, 'datasets', self.slug)

    def get_absolute_url(self):
        return reverse_lazy('core:dataset-detail', args=[self.pk])


class DataTableQuerySet(models.query.QuerySet):
    pass


class DataTableManager(PassThroughManager):

    use_for_related_fields = True

    def create(self, *args, **kwargs):
        dataset = kwargs.get('dataset', None)
        if dataset is None:
            raise ValidationError("Every DataTable must be associated with a Dataset")
        kwargs.setdefault('creator', dataset.creator)
        return super(DataTableManager, self).create(*args, **kwargs)


class DataTable(MiracleMetadataMixin, DatasetConnectionMixin):

    """
    DataTable.name will be used for the internal RDBMS table name in the miracle_data database
    DataTable.full_name is the user assigned data table name (e.g., CSV filename, Excel sheet name, user supplied name)
    """

    dataset = models.ForeignKey(Dataset, related_name='tables')
    datafile = models.FileField(help_text=_("The archived plaintext file corresponding to this DataTable"))
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

    datatable = models.ForeignKey(DataTable, related_name='columns')
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


class MiracleUser(models.Model):
    user = models.OneToOneField(User, related_name='miracle_user')
    institution = models.CharField(max_length=512)

    def get_absolute_url(self):
        return reverse_lazy('core:profile')

    def __unicode__(self):
        return u'{} {}'.format(self.user, self.institution)


class ActivityLogQuerySet(models.query.QuerySet):

    def for_user(self, user, **kwargs):
        return self.filter(creator=user, **kwargs)


class ActivityLogManager(PassThroughManager):

    def scheduled(self, message):
        return self.create(message=message, action=ActivityLog.ActionType.SCHEDULED)

    def log(self, message):
        return self.create(message=message)

    def log_user(self, user, message):
        return self.create(creator=user, message=message, action=ActivityLog.ActionType.USER)


class ActivityLog(models.Model):

    ActionType = Choices(
        ('SYSTEM', _('System Activity')),
        ('USER', _('User Activity')),
        ('SCHEDULED', _('Scheduled System Activity')),
    )
    message = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(User, blank=True, null=True)
    action = models.CharField(max_length=32, choices=ActionType, default=ActionType.SYSTEM)
    objects = ActivityLogManager.for_queryset_class(ActivityLogQuerySet)()

    def __unicode__(self):
        return u"{} {} {}".format(self.creator, self.action, self.message)
