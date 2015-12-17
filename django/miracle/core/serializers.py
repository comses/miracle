from django.contrib.auth.models import User
from django.utils import timezone
from collections import defaultdict
from rest_framework import serializers
from .models import (Project, DatasetFile, Dataset, DataAnalysisScript, AnalysisOutput, AnalysisOutputFile, Author)

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


class OutputFileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='output_file.name')
    url = serializers.URLField(read_only=True, source='output_file.url')

    class Meta:
        model = AnalysisOutputFile
        fields = ('id', 'metadata', 'url', 'name')


class AnalysisOutputSerializer(serializers.ModelSerializer):
    analysis = serializers.StringRelatedField()
    files = OutputFileSerializer(many=True)

    class Meta:
        model = AnalysisOutput
        fields = ('id', 'name', 'date_created', 'creator', 'analysis', 'parameter_values_text', 'files')


class AuthorSerializer(serializers.ModelSerializer):

    user = UserSerializer()

    class Meta:
        model = Author


class AnalysisSerializer(serializers.HyperlinkedModelSerializer):
    project = serializers.ReadOnlyField(source='project.name')
    parameters = serializers.ReadOnlyField(source='input_parameters')
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
                  'file_type', 'parameters', 'url', 'authors', 'outputs', 'job_status')


class DatasetSerializer(serializers.HyperlinkedModelSerializer):
    project = serializers.ReadOnlyField(source='project.name')

    class Meta:
        model = Dataset
        extra_kwargs = {
            'url': {'view_name': 'core:dataset-detail'}
        }
        fields = ('id', 'name', 'project', 'url')


class DatasetFileSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = DatasetFile
        fields = ('id', 'archived_file', 'ignored')


class ProjectSerializer(serializers.ModelSerializer):
    group_members = StringListField()
    group = serializers.StringRelatedField()
    creator = serializers.SlugRelatedField(slug_field='email', read_only=True)
    published = serializers.BooleanField()
    published_on = serializers.DateTimeField(format='%b %d, %Y %H:%M:%S %Z', read_only=True)
    date_created = serializers.DateTimeField(format='%b %d, %Y %H:%M:%S %Z', read_only=True)
    detail_url = serializers.CharField(source='get_absolute_url', read_only=True)
    status = serializers.ReadOnlyField()
    number_of_datasets = serializers.IntegerField(read_only=True)
    datasets = DatasetSerializer(many=True, read_only=True)
    analyses = AnalysisSerializer(many=True, read_only=True)

    def validate_group_members(self, value):
        logger.debug("validating group members with value: %s", value)
        return value

    def create(self, validated_data):
        logger.debug("creating project with data %s", validated_data)
        # FIXME: slice validated_data to only take out the name, description, and whether or not it's been published
        group_members = validated_data.pop('group_members')
        published = validated_data.pop('published', False)
        creator = validated_data.get('creator')
        if published:
            validated_data['published_on'] = timezone.now()
            validated_data['published_by'] = creator
        project = Project.objects.create(**validated_data)
        if group_members:
            users = User.objects.filter(username__in=group_members)
            logger.debug("setting group members: %s", users)
            project.set_group_members(User.objects.filter(username__in=group_members))
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

    @property
    def modified_data(self):
        return getattr(self, '_modified_data', defaultdict(tuple))

    @property
    def modified_data_text(self):
        def _convert(v):
            return 'None' if not v else v
        md = self.modified_data
        md_list = ['{}: {} -> {}'.format(key, _convert(pair[0]), _convert(pair[1])) for key, pair in md.items()]
        return ' | '.join(md_list)

    class Meta:
        model = Project
