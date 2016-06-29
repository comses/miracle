from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

from miracle.core.models import Project

import csv
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ''' Manages creation and deletion of multiple demo users, associating them with a project, and emitting
    their credentials to a csv file'''
    DEFAULT_DEMO_GROUP = 'demo-group'

    def add_arguments(self, parser):
        parser.add_argument('--purge',
                            action='store_true',
                            help='Purge all demo users')
        parser.add_argument('--number',
                            default=35,
                            type=int,
                            help='Number of demo users to create')
        parser.add_argument('--prefix',
                            default='demo',
                            help='Username prefix, will have sequential numbers appended to it')
        parser.add_argument('--suffix',
                            default='mailinator.com',
                            help='Base email suffix')
        parser.add_argument('--outfile',
                            default='miracle-demo-users.csv',
                            help='Output file with created demo user credentials')
        parser.add_argument('--slug',
                            default='luxedemo',
                            help='Shortname for the project that these demo users will have writable access')

    def handle(self, *args, **options):
        purge = options['purge']
        number_of_users = options['number']
        prefix = options['prefix']
        email_suffix = options['suffix']
        outfile = options['outfile']
        slug = options['slug']
        if purge:
            output = User.objects.filter(groups__name=Command.DEFAULT_DEMO_GROUP).delete()
            logger.debug("Purged all demo users: %s", output)
            return
        else:
            demo_group, created = Group.objects.get_or_create(name=Command.DEFAULT_DEMO_GROUP)
            project = Project.objects.get(slug=slug)
            with open(outfile, 'wb') as f:
                writer = csv.DictWriter(f, fieldnames=['username', 'password', 'email'])
                writer.writeheader()
                for i in range(0, number_of_users):
                    username = '{0}{1}'.format(prefix, i)
                    email = '{0}@{1}'.format(username, email_suffix)
                    password = User.objects.make_random_password(length=6)
                    user = User.objects.create_user(username=username, password=password, email=email, first_name='Demo User',
                                                    last_name='#{0}'.format(i))
                    user.groups.add(demo_group)
                    project.add_group_member(user)
                    logger.debug("added user %s to project %s and demo group %s", user, project, demo_group)
                    writer.writerow({'username': username, 'password': password, 'email': email})
