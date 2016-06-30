from django.contrib.auth.models import User
from django.core.validators import slug_re
from django.db import transaction
from django.utils import timezone, text
from django_comments.models import Comment
from collections import defaultdict
from rest_framework import serializers

from .models import (Project, DataFile, DataColumn, DataTableGroup, DataAnalysisScript, AnalysisOutput, AnalysisOutputFile,
                     AnalysisParameter, ParameterValue, Author, ActivityLog)

import logging

logger = logging.getLogger(__name__)


class StringListField(serializers.ListField):
    child = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField()
    email = serializers.ReadOnlyField()
    full_name = serializers.ReadOnlyField(source='get_full_name')

    class Meta:
        model = User
        fields = ('username', 'email', 'full_name')


class ParameterValueSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='parameter.name')
    label = serializers.CharField(read_only=True, source='parameter.label')

    class Meta:
        model = ParameterValue
        fields = ('id', 'name', 'label', 'value')


class OutputFileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='basename')
    url = serializers.URLField(read_only=True, source='get_absolute_url')

    class Meta:
        model = AnalysisOutputFile
        fields = ('id', 'metadata', 'url', 'name')


class AnalysisOutputSerializer(serializers.ModelSerializer):
    analysis = serializers.StringRelatedField()
    files = OutputFileSerializer(many=True)
    parameter_values = ParameterValueSerializer(many=True, read_only=True)
    creator = serializers.SlugRelatedField(slug_field='email', read_only=True)

    class Meta:
        model = AnalysisOutput
        fields = ('id', 'name', 'date_created', 'creator', 'analysis', 'parameter_values', 'files')


class AuthorSerializer(serializers.ModelSerializer):

    user = UserSerializer()

    class Meta:
        model = Author


class AnalysisParameterSerializer(serializers.ModelSerializer):
    value = serializers.ReadOnlyField(source='default_value')
    html_input_type = serializers.SerializerMethodField()
    html_input_type_converter = defaultdict(lambda: 'text', {
        'integer': 'number',
        'numeric': 'number',
        'character': 'text',
        'logical': 'checkbox',  # FIXME: needs additional UI support for checkboxes
    })

    def get_html_input_type(self, obj):
        return AnalysisParameterSerializer.html_input_type_converter[obj.data_type]

    class Meta:
        model = AnalysisParameter
        fields = ('id', 'name', 'label', 'data_type', 'description', 'value', 'html_input_type', 'value_list',
                  'value_range')


class DataAnalysisScriptSerializer(serializers.HyperlinkedModelSerializer):
    project = serializers.ReadOnlyField(source='project.name')
    parameters = AnalysisParameterSerializer(many=True)
    authors = AuthorSerializer(many=True)
    outputs = AnalysisOutputSerializer(many=True, read_only=True)
    job_status = serializers.SerializerMethodField()

    def get_job_status(self, obj):
        return 'IDLE'

    class Meta:
        model = DataAnalysisScript
        extra_kwargs = {
            'url': {'view_name': 'core:analysis-detail'}
        }
        fields = ('id', 'name', 'full_name', 'date_created', 'last_modified', 'description', 'project',
                  'file_type', 'parameters', 'url', 'authors', 'outputs', 'job_status', 'enabled')


class DataColumnSerializer(serializers.ModelSerializer):

    data_table_group = serializers.ReadOnlyField(source='data_table_group.name')

    class Meta:
        model = DataColumn


class DataTableGroupSerializer(serializers.HyperlinkedModelSerializer):
    project = serializers.ReadOnlyField(source='project.name')
    columns = DataColumnSerializer(many=True, read_only=True)
    number_of_files = serializers.SerializerMethodField(read_only=True)
    number_of_columns = serializers.SerializerMethodField(read_only=True)

    def get_number_of_columns(self, data_table_group):
        return data_table_group.columns.count()

    def get_number_of_files(self, data_table_group):
        return data_table_group.files.count()

    class Meta:
        model = DataTableGroup
        extra_kwargs = {
            'url': {'view_name': 'core:data-group-detail'}
        }
        fields = ('id', 'name', 'full_name', 'project', 'url', 'columns', 'number_of_files', 'number_of_columns')


class DataFileSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = DataFile
        fields = ('id', 'archived_file', 'ignored')


class CommentSerializer(serializers.ModelSerializer):
    submit_date = serializers.DateTimeField(format='%b %d, %Y %H:%M:%S %Z', read_only=True)

    class Meta:
        model = Comment
        fields = ('user_name', 'user_email', 'comment', 'submit_date')

class ActivityLogSerializer(serializers.ModelSerializer):
    creator = serializers.SlugRelatedField(slug_field='username', read_only=True)
    date_created = serializers.DateTimeField(format='%b %d, %Y %H:%M:%S %Z', read_only=True)
    project = serializers.SlugRelatedField(slug_field='slug', read_only=True)

    class Meta:
        model = ActivityLog
        fields = ('creator', 'action', 'message', 'date_created', 'data', 'project')

class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    group_members = StringListField()
    group = serializers.StringRelatedField()
    creator = serializers.SlugRelatedField(slug_field='email', read_only=True)
    published = serializers.BooleanField()
    published_on = serializers.DateTimeField(format='%b %d, %Y %H:%M:%S %Z', read_only=True)
    date_created = serializers.DateTimeField(format='%b %d, %Y %H:%M:%S %Z', read_only=True)
    status = serializers.ReadOnlyField()
    number_of_datasets = serializers.IntegerField(read_only=True)
    data_table_groups = DataTableGroupSerializer(many=True, read_only=True)
    analyses = DataAnalysisScriptSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    slug = serializers.CharField(allow_blank=True)
    recent_activity = ActivityLogSerializer(many=True, read_only=True, source='activity_logs')

    def validate_group_members(self, value):
        logger.debug("validating group members with value: %s", value)
        return value

    def create(self, validated_data):
        logger.debug("creating project with data %s", validated_data)
        # FIXME: slice validated_data to only take out the name, description, and whether or not it's been published
        group_members = validated_data.pop('group_members')
        published = validated_data.pop('published', False)
        creator = validated_data.get('creator')
        slug = validated_data.get('slug')
        if published:
            validated_data['published_on'] = timezone.now()
            validated_data['published_by'] = creator
        project = Project.objects.create(**validated_data)
        if group_members:
            users = User.objects.filter(username__in=group_members)
            logger.debug("setting group members: %s", users)
            project.set_group_members(User.objects.filter(username__in=group_members))
            project.save()
        if slug:
            logger.debug("Setting slug explicitly to %s", slug)
            project.slug = slug
            project.save()
        return project

    def update(self, instance, validated_data):
        logger.debug("updating instance %s with validated data %s", instance, validated_data)
        self._modified_data = defaultdict(tuple)
        incoming_group_members = validated_data.pop('group_members')
        user = validated_data.pop('user')
        published = validated_data.pop('published')
        for attr, value in validated_data.items():
            original_value = getattr(instance, attr, None)
            if original_value != value:
                logger.debug("original value %s (%s) appears to be different from incoming value %s (%s)", original_value,
                             type(original_value), value, type(value))
                self._modified_data[attr] = (original_value, value)
                setattr(instance, attr, value)
        if published and not instance.published:
            self._modified_data['published'] = (True, False)
            instance.publish(user, defer=True)
        elif not published and instance.published:
            self._modified_data['published'] = (False, True)
            instance.unpublish(user, defer=True)
        existing_group_members = frozenset(instance.group_members)
        if existing_group_members.symmetric_difference(incoming_group_members):
            self._modified_data['group_members'] = (existing_group_members, incoming_group_members)
            users = User.objects.filter(username__in=incoming_group_members)
            instance.set_group_members(users)
        instance.save()
        return instance

    @transaction.atomic
    def validate(self, data):
        slug = data['slug']
        name = data['name']
        pk = -1 if self.instance is None else self.instance.pk
        if not slug:
            logger.debug("slugifying name %s", name)
            slug = text.slugify(name)
        # check if slug exists in project table already
        if not slug_re.match(slug):
            raise serializers.ValidationError("Please enter a valid short name (no spaces) or leave blank to autogenerate one.")
        elif Project.objects.filter(slug=slug).exclude(pk=pk).exists():
            raise serializers.ValidationError("Sorry, this short name has already been taken. Please choose another.")
        else:
            data.update(slug=slug)
        return data

    @property
    def modified_data(self):
        return getattr(self, '_modified_data', defaultdict(tuple))

    @property
    def modified_data_text(self):
        def _convert(v):
            return 'None' if not v else v
        md = self.modified_data
        md_list = ['{}:{}->{}'.format(key, _convert(pair[0]), _convert(pair[1])) for key, pair in md.items()]
        return 'Metadata update - {0}'.format(' | '.join(md_list))

    class Meta:
        model = Project
        fields = ('id', 'url', 'group_members', 'group', 'creator', 'published', 'published_on', 'date_created',
                  'status', 'number_of_datasets', 'data_table_groups', 'analyses', 'slug', 'description', 'name',
                  'comments', 'recent_activity', 'submitted_archive'
                  )
        extra_kwargs = {
            'url': {'view_name': 'core:project-detail', 'lookup_field': 'slug'},
        }
