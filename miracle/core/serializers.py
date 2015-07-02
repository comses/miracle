from django.contrib.auth.models import User
from collections import defaultdict
from rest_framework import serializers
from .models import (Project, Dataset,)

import logging

logger = logging.getLogger(__name__)


class StringListField(serializers.ListField):
    child = serializers.CharField()


class ProjectSerializer(serializers.ModelSerializer):
    group_members = StringListField()
    group = serializers.StringRelatedField()
    creator = serializers.SlugRelatedField(slug_field='email', read_only=True)
    published = serializers.BooleanField()
    published_on = serializers.DateTimeField(format='%b %d, %Y %H:%M:%S', read_only=True)
    date_created = serializers.DateTimeField(format='%b %d, %Y %H:%M:%S', read_only=True)
    detail_url = serializers.CharField(source='get_absolute_url', read_only=True)

    def create(self, validated_data):
        logger.debug("creating project with data %s", validated_data)
        group_members = validated_data.pop('group_members')
        project = Project.objects.create(**validated_data)
        project.set_group_members(User.objects.filter(username__in=group_members))
        return project

    def update(self, instance, validated_data):
        logger.debug("updating instance %s with validated data %s", instance, validated_data)
        self._modified_data = defaultdict(tuple)
        group_members = validated_data.pop('group_members')
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
        if existing_group_members.difference(group_members):
            logger.debug("updating group members for %s from %s to %s", instance, existing_group_members, group_members)
            users = User.objects.filter(username__in=group_members)
            instance.set_group_members(users)
        instance.save()
        return instance

    @property
    def modified_data(self):
        return getattr(self, '_modified_data', defaultdict(tuple))

    @property
    def modified_data_text(self):
        _convert = lambda v: 'None' if not v else v
        md = self.modified_data
        md_list = ['{}: {} -> {}'.format(key, _convert(pair[0]), _convert(pair[1])) for key, pair in md.items()]
        return ' | '.join(md_list)

    class Meta:
        model = Project


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
