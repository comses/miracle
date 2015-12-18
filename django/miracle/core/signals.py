from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Project, Group


@receiver(post_save, sender=Project)
@transaction.atomic
def create_project_group(sender, instance, created, raw, using, update_fields, **kwargs):
    """
    Ensure that a permissions Group (named via Project.group_name) is always available for basic per-Project permissions
    management
    """
    if created or instance.group is None:
        group, created = Group.objects.get_or_create(name=instance.group_name)
        group.user_set.add(instance.creator)
        instance.group = group
        instance.save()
