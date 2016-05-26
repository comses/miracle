from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import logging
import os

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Create an project from an uploaded archive.
    """
    help = 'Import a project'

    def add_arguments(self, parser):
        parser.add_argument('--username',
                            dest='username',
                            default=os.environ.get('MIRACLE_USER'),
                            help='Initial admin username')
        parser.add_argument('--password',
                            dest='password',
                            default=os.environ.get('MIRACLE_USER_PASSWORD', settings.SECRET_KEY),
                            help='Initial admin password')
        parser.add_argument('email',
                            dest='email',
                            default=os.environ.get('MIRACLE_EMAIL', settings.SERVER_EMAIL),
                            help='Initial admin email')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']
        if User.objects.filter(username=username).exists():
            logger.debug("Admin user already exists: %s (%s)", username, email)
        else:
            User.objects.create_superuser(username=username, password=password, email=email)
            logger.debug("Created admin user %s (%s)", username, email)
