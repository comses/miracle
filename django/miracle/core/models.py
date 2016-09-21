from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse_lazy
from django.db import models, connections, transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from django_comments.models import Comment
from django_extensions.db.fields import AutoSlugField
from model_utils import Choices

import logging
import hashlib
import os
import pathlib2
import re
import shutil
import utils

from pygments.lexers import guess_lexer_for_filename
from pygments.lexers.special import TextLexer

from .deployr import DeployrAPI

logger = logging.getLogger(__name__)


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
        # DataColumn (i.e., DataTable names must be unique across all DataTables, DataColumn names must be
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
    name = models.CharField(max_length=255)
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
    def publishing_status(self):
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
            ActivityLog.objects.log_user(user, 'Published {0} on {1}'.format(str(self), self.published_on))

    def unpublish(self, user, defer=False):
        original_published_on = self.published_on
        if original_published_on:
            self.published_on = None
            self.published_by = None
            if not defer:
                self.save()
            ActivityLog.objects.log_user(user, 'Unpublished {0} (originally published on {1})'.format(str(self), original_published_on))

    def deactivate(self, user):
        if not self.deleted_on:
            self.deleted_on = timezone.now()
            self.deleted_by = user
            self.save()
            ActivityLog.objects.log_user(user, 'Deactivated {0} on {1}'.format(str(self), self.deleted_on))

    def activate(self, user):
        original_deleted_on = self.deleted_on
        if original_deleted_on:
            self.deleted_on = None
            self.deleted_by = None
            self.save()
            ActivityLog.objects.log_user(user, 'Reactivated {0} (originally deactivated on {1})'.format(str(self), original_deleted_on))

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


def project_archive_path(instance, filename):
    slug = str(instance.slug)
    hash_dir = hashlib.sha1(slug).hexdigest()
    return os.path.join(hash_dir, filename)

class Project(MiracleMetadataMixin):

    # FIXME: may need to replace this with a simple SlugField, see https://github.com/comses/miracle/issues/41
    slug = AutoSlugField(populate_from='name', unique=True)
    group = models.OneToOneField(Group, editable=False,
                                 help_text=_("Members of this group can edit this project's datasets and metadata"),
                                 null=True)
    submitted_archive = models.FileField(help_text=_("The uploaded zipfile containing all data and scripts for this Project"), null=True, blank=True,
                                         upload_to=project_archive_path,
                                         storage=FileSystemStorage(location=settings.ARCHIVE_DIRECTORY,
                                                                   base_url=settings.ARCHIVE_URL))
    objects = ProjectQuerySet.as_manager()

    @property
    def archive_path(self):
        return self.submitted_archive.path

    @property
    def comments(self):
        return Comment.objects.for_model(self)

    @property
    def packrat_path(self):
        return os.path.join(settings.PACKRAT_DIRECTORY, str(self.slug))

    @property
    def project_path(self):
        return os.path.join(settings.PROJECT_DIRECTORY, str(self.slug))

    def package_dependencies(self):
        lock_file_path = os.path.join(self.packrat_path, 'packrat.lock')
        if os.path.exists(lock_file_path):
            with open(lock_file_path) as f:
                lock_file_contents = f.read()
                return utils.highlight(lock_file_contents, TextLexer())
        else:
            return "No packrat.lock file found"

    def archive(self, incoming_file):
        p = pathlib2.Path(incoming_file.name)
        simplified_filename = ''.join([self.slug] + p.suffixes)
        self.submitted_archive.save(simplified_filename, incoming_file)

    def clear_archive(self, user):
        self.log("Clear project archive", user)
        # delete all data table groups, data analysis scripts, and files.
        with transaction.atomic():
            self.data_table_groups.all().delete()
            self.analyses.all().delete()
            self.files.all().delete()
            self.submitted_archive.delete()
        # FIXME: add error handlers
        logger.debug("Deleting extracted project tree %s", self.project_path)
        shutil.rmtree(self.project_path, True)
        logger.debug("Deleting extracted packrat path %s", self.packrat_path)
        shutil.rmtree(self.packrat_path, True)
        DeployrAPI.clear_project_archive(self)

    @property
    def group_name(self):
        # unique name to manage permissions for this project
        # FIXME: should probably use slug instead
        return u'{} Group #{}'.format(self.name, self.pk)

    @property
    def group_members(self):
        return self.group.user_set.values_list('username', flat=True)

    def log(self, message, user=None, data=None):
        logger.debug("(user %s modifying project %s) %s with data %s", user, self, message, data)
        return ActivityLog.objects.log_project_update(user, self, message, data)

    def has_admin_privileges(self, user):
        return user.is_superuser and self.has_group_member(user)

    def has_group_member(self, user):
        return self.creator == user or user.groups.filter(name=self.group_name).exists()

    def add_group_member(self, user):
        return user.groups.add(self.group)

    def set_group_members(self, users):
        self.group.user_set = users

    def remove_group_member(self, user):
        return user.groups.remove(self.group)

    def bookmark_for(self, user=None):
        if user is None:
            raise ValueError("No user specified for bookmarking this project")
        bookmarked_project, created = BookmarkedProject.objects.get_or_create(project=self, user=user)
        return bookmarked_project

    @property
    def number_of_datasets(self):
        return self.data_table_groups.count()

    @property
    def outputs(self):
        return AnalysisOutput.objects.filter(analysis__project=self)

    def get_absolute_url(self):
        return reverse_lazy('core:project-detail', args=[self.slug])

    class Meta(object):
        permissions = (
            ('view_project', 'Can view this project'),
            ('edit_project', 'Can edit this project'),
            ('admin_project', 'Full admin over this project'),
            ('create_projects', 'Can create projects'),
        )


class BookmarkedProject(models.Model):

    project = models.ForeignKey(Project)
    user = models.ForeignKey(User, related_name='bookmarked_projects')

    class Meta:
        unique_together = ('project', 'user')


class Author(models.Model):

    user = models.OneToOneField(User)
    attributes = JSONField(null=True, blank=True)

    def __unicode__(self):
        return self.user.email


class DataAnalysisScript(MiracleMetadataMixin):

    FileType = Choices(
        ('R', _('R script')),
        ('Julia', _('Julia script')),
        ('Python', _('Python script')),
        ('Perl', _('Perl script')),
    )

    slug = AutoSlugField(populate_from='name', unique=True, overwrite=True)
    project = models.ForeignKey(Project, related_name="analyses")
    archived_file = models.FileField(help_text=_("The archived file corresponding to this AnalysisScript"))
    provenance = JSONField(null=True, blank=True)
    file_type = models.CharField(max_length=128, choices=FileType, default=FileType.R)
    authors = models.ManyToManyField(Author, blank=True)
    enabled = models.BooleanField(default=False)

    @property
    def default_output_name(self):
        output_name = self.full_name if self.full_name else self.name
        return u"{} output".format(output_name)

    @property
    def input_parameters(self):
        # returns a list of dicts for easier JSON consumption
        return [dict(name=k, **v) for k, v in self.get_deployr_parameters_dict().items()]

    @staticmethod
    def to_deployr_input_parameters(parameters_list):
        """
        Converts list of parameters [{'name': 'fooparamname', 'value': 'bar', 'label': 'baz', ...}, ...] into a single dict
        object for consumption by the DeployR API of the form
        { 'fooparamname': {'value: 'bar', 'label': 'baz', ...}, ... }
        NOTE: Assumes that value has already been set on the parameter.
        """
        deployr_input_parameters = {}
        for parameter_dict in parameters_list:
            name = parameter_dict.pop('name')
            parameter_dict.pop('id')
            rclass = parameter_dict.pop('data_type')
            parameter_dict['rclass'] = rclass
            # assign the rest of the parameter attributes dict to the param name as is
            deployr_input_parameters[name] = parameter_dict
        return deployr_input_parameters

    def add_parameters(self, parameters):
        """ parameters is a list of dictionaries with (currently) DeployR specific keys """
        for parameter in parameters:
            self.parameters.create(
                name=parameter["name"],
                label=parameter["label"],
                data_type=parameter["render"],
                default_value=str(parameter["default"]),
                value_list=parameter.get("valueList"),
                value_range=parameter.get("valueRange"),
            )

    def get_deployr_parameters_dict(self, values=None):
        if values is None:
            values = {}
        return dict(
            (p.name, {'label': p.label, 'type': 'primitive', 'rclass': p.data_type, 'value': values.get(p.name, p.default_value)})
            for p in self.parameters.all()
        )

    @property
    def basename(self):
        return os.path.basename(str(self.archived_file))

    @property
    def path(self):
        return os.path.join(settings.PROJECT_DIRECTORY, self.project.slug, str(self.archived_file))

    def archived_file_contents(self):
        code_path = self.path
        with open(code_path, 'rb') as f:
            code_file_contents = f.read()
        return code_file_contents

    def archived_file_contents_highlighted(self):
        contents = self.archived_file_contents()
        lexer = guess_lexer_for_filename(self.path, contents)
        contents_highlighted = utils.highlight(contents, lexer)
        return contents_highlighted

    def __unicode__(self):
        return u'{} {}'.format(self.name, self.archived_file)

    class Meta:
        ordering = ['date_created']


class AnalysisParameter(models.Model):

    # XXX: currently 1:1 with R data types, support for other types of analysis scripts require additional mappings
    # FIXME: add array and range types
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

    analysis = models.ForeignKey(DataAnalysisScript, related_name='parameters')
    name = models.CharField(max_length=255, help_text=_("Input parameter variable name used in this analysis script."))
    label = models.CharField(max_length=255, help_text=_("Human-friendly label for this parameter."), blank=True)
    description = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    data_type = models.CharField(max_length=128, choices=ParameterType, default=ParameterType.character)
    allow_multiple_values = models.BooleanField(help_text=_("True if this parameter allows multiple values"),
                                                default=False)
    default_value = models.CharField(max_length=255, blank=True,
                                     help_text=_("default value for this analysis input parameter"))
    # use JSONField instead of django.contrib.postgres.fields.ArrayField because different rows have potentially
    # different element types
    value_list = JSONField(help_text=_("List of possible values for this parameter"), null=True, blank=True)
    value_range = JSONField(help_text=_("Range of values in the form of start, end, step."), null=True, blank=True)

    def convert(self, value):
        return AnalysisParameter.TYPE_CONVERTERS[self.data_type](value)

    def __unicode__(self):
        return u'{} ({})'.format(self.label, self.name)


class AnalysisOutput(models.Model):

    analysis = models.ForeignKey(DataAnalysisScript, related_name='outputs')
    name = models.CharField(max_length=255, help_text=_("User assigned name for this script run"))
    description = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(User)
    response = JSONField(help_text=_("Internal raw HTTP response from executing the script against DeployR/OpenCPU"),
                         null=True, blank=True)

    @property
    def project(self):
        return self.analysis.project

    def __unicode__(self):
        return u'[{}] output from running {} on {} by {}'.format(
            self.name, self.analysis, self.date_created, self.creator
        )

    class Meta:
        ordering = ['-date_created']


class ParameterValue(models.Model):

    parameter = models.ForeignKey(AnalysisParameter)
    output = models.ForeignKey(AnalysisOutput, related_name='parameter_values')
    value = models.CharField(max_length=255, help_text=_("Assigned value for the given input parameter"))


def _analysis_output_path(instance, filename):
    return os.path.join(instance.folder, 'outputs', filename)

PROJECT_STORAGE = FileSystemStorage(location=settings.PROJECT_DIRECTORY)

class AnalysisOutputFile(models.Model):

    output = models.ForeignKey(AnalysisOutput, related_name='files')
    output_file = models.FileField(upload_to=_analysis_output_path, storage=PROJECT_STORAGE)
    metadata = JSONField(help_text=_("Additional metadata provided by analysis execution engine"), null=True, blank=True)

    @property
    def folder(self):
        return self.output.project.project_path

    @property
    def path(self):
        return self.output_file.path

    @property
    def basename(self):
        return os.path.basename(self.path)

    @property
    def get_absolute_url(self):
        return reverse_lazy('core:output-download', args=[self.pk])

    def __unicode__(self):
        return u"output file {}".format(self.output_file)


class DataTableGroupQuerySet(models.query.QuerySet):

    def viewable(self, user, *args, **kwargs):
        """
        DataTableGroups are viewable when they:
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


class DataTableGroupManager(models.Manager):

    use_for_related_fields = True

    def create_data_group(self, *args, **kwargs):
        project = kwargs.get('project')
        if project is None:
            raise ValidationError("DataTableGroups must be associated with a Project")
        kwargs.setdefault('creator', project.creator)
        return DataTableGroup.objects.create(*args, **kwargs)


class DataTableGroup(MiracleMetadataMixin):
    """
    A DataTableGroup wraps schema + metadata for associated DataColumns. For example, an Excel file with N sheets where
    each sheet has a different schema would be represented as N DataTableGroups, and be archived with a single CSV
    DataFile per sheet. A directory with 600 data files that all share the same schema would be represented as a single
    DataTableGroup with 600 DataFiles and all share the same DataColumn relationships + metadata.

    We aren't building a true digital preservation repository, we may get mileage out of the OAIS reference model
    notions of Submission Information Packages, Archival Information Packages, and Dissemination Information Packages
    (http://www2.archivists.org/_groups/standards-committee/open-archival-information-system-oais)
    """

    slug = AutoSlugField(populate_from='name', unique=True, overwrite=True)
    project = models.ForeignKey(Project, related_name="data_table_groups")
    provenance = JSONField(help_text=_("Provenance metadata for this DataTableGroup, applicable to all children"),
                           null=True, blank=True)
    authors = models.ManyToManyField(Author)
    analyses = models.ManyToManyField(DataAnalysisScript)
    data_type = models.CharField(max_length=50, blank=True)
    schema = JSONField(help_text=_("Column schema for this DataTableGroup, applicable to all child DataTables"),
                       null=True, blank=True)
    external_url = models.URLField(blank=True)

    objects = DataTableGroupManager.from_queryset(DataTableGroupQuerySet)()

    @property
    def uploads_path(self):
        return os.path.join(self.project.uploads_path, 'data', self.slug)

    def get_absolute_url(self):
        return reverse_lazy('core:dataset-detail', args=[self.pk])


class DataFile(models.Model):

    ignored = models.BooleanField(default=False, help_text=_('Set to true if this file should be ignored'))
    project = models.ForeignKey(Project, related_name='files')
    data_table_group = models.ForeignKey(DataTableGroup, null=True, related_name='files')
    archived_file = models.FileField(help_text=_("Archival data information package file"))


class DataColumn(models.Model):

    """
    Metadata for a Column in a given DataTableGroup to capture basic type and description info.
    """
    # FIXME: revisit + refine these data types
    DataType = Choices(
        ('bigint', _('integer')),
        ('boolean', _('boolean')),
        ('decimal', _('floating point number')),  # worse performance than float but avoids rounding errors
        ('text', _('text')),
        ('date', _('date'))
    )

    data_table_group = models.ForeignKey(DataTableGroup, related_name='columns')
    name = models.CharField(max_length=64, blank=True, help_text=_("Actual column name"))
    full_name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    data_type = models.CharField(max_length=128, choices=DataType, default=DataType.text)
    table_order = models.PositiveIntegerField(default=1, help_text=_("This column's one-based index into the table"))

    def all_values(self, distinct=False):
        ''' returns a list resulting from select name from data table using miracle_data database '''
        statement = "SELECT {} {} FROM {}".format('DISTINCT' if distinct else '', self.name, self.table.name)
        self.cursor.execute(statement)
        return self.cursor.fetchall()

    @property
    def project(self):
        return self.data_table_group.project

    def get_absolute_url(self):
        return reverse_lazy('core:data-column-detail', args=[self.pk])

    def __unicode__(self):
        return u'{0} (type: {1})'.format(self.name, self.data_type)

    class Meta:
        ordering = ['table_order']


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


class ActivityLogManager(models.Manager):

    def scheduled(self, message):
        return self.create(message=message, action=ActivityLog.ActionType.SCHEDULED)

    def log(self, message):
        return self.create(message=message)

    def log_project_update(self, user=None, project=None, message=None, action=None):
        return self.create(creator=user, project=project, message=message, action=ActivityLog.ActionType.USER)

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
    project = models.ForeignKey(Project, blank=True, null=True, related_name='activity_logs')
    action = models.CharField(max_length=32, choices=ActionType, default=ActionType.SYSTEM)
    data = JSONField(blank=True, null=True)

    objects = ActivityLogManager.from_queryset(ActivityLogQuerySet)()

    class Meta:
        ordering = ['-date_created']

    def __unicode__(self):
        return u"{0} {1} {2}".format(self.action, self.creator, self.message)
