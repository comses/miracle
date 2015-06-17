from django.contrib.auth.models import User
from rest_framework import serializers
from .models import (Project, Dataset,)

import logging

logger = logging.getLogger(__name__)


class GroupMemberSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=30)


class ProjectSerializer(serializers.ModelSerializer):
    group_members = GroupMemberSerializer(many=True)
    group = serializers.StringRelatedField()
    creator = serializers.SlugRelatedField(slug_field='email', read_only=True)

    def validate_group_members(self, group_members):
        incoming_usernames = frozenset([gm_dict['username'] for gm_dict in group_members])
        matched_usernames = User.objects.filter(username__in=incoming_usernames).values_list('username', flat=True)
        unmatched = incoming_usernames.difference(matched_usernames)
        if unmatched:
            raise serializers.ValidationError("No users found with usernames {}".format(unmatched))
        return matched_usernames

    def create(self, validated_data):
        group_members = validated_data.pop('group_members')
        project = Project.objects.create(**validated_data)
        project.set_group_members(User.objects.filter(username__in=group_members))
        return project

    def update(self, instance, validated_data):
        group_members = validated_data.pop('group_members')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        logger.debug("updating group members for %s from %s to %s", instance, instance.group.user_set.all(),
                     group_members)
        instance.set_group_members(User.objects.filter(username__in=group_members))
        return instance

    class Meta:
        model = Project


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
