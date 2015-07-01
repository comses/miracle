from django.contrib.auth.models import User
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
        group_members = validated_data.pop('group_members')
        user = validated_data.pop('user')
        logger.debug("group members: %s", group_members)
        published = validated_data.pop('published')
        for attr, value in validated_data.items():
            original_value = getattr(instance, attr, None)
            if original_value != value:
                logger.debug("setting attr %s:%s", attr, value)
                setattr(instance, attr, value)
        if published and not instance.published:
            instance.publish(user, defer=True)
        elif not published and instance.published:
            instance.unpublish(user, defer=True)
        existing_group_members = frozenset(instance.group_members)
        logger.debug("existing group members %s", existing_group_members)
        if existing_group_members.difference(group_members):
            logger.debug("updating group members for %s from %s to %s", instance, existing_group_members, group_members)
            instance.set_group_members(User.objects.filter(username__in=group_members))
        instance.save()
        return instance

    class Meta:
        model = Project


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
