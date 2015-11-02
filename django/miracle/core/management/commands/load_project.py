from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from ...metadata_interface import add_project
from ...models import Project, User
import logging
import os

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Create an project from an uploaded archive.
    """
    help = 'Import a project'

    def add_arguments(self, parser):
        parser.add_argument('--creator',
                            nargs=1,
                            type=str,
                            help='The creator of the project')
        parser.add_argument('--project',
                            nargs=1,
                            type=str,
                            help='The project')
        parser.add_argument('archive_file',
                            nargs=1,
                            type=str,
                            help='The archived project file you want to import')

    def handle(self, *args, **options):
        logger.debug(args)
        logger.debug(options)

        creator_name = options['creator'][0]
        project_name = options['project'][0]
        archive_path = options['archive_file'][0]

        self.extract(creator_name, project_name, archive_path)
        self.stdout.write("Successfully imported data")

    @staticmethod
    def create_user(username='testuser', email='miracle-test@mailinator.com',
                    first_name='Default', last_name='Testuser', password='test'):
        user = User.objects.get(username=username)
        if not user:
            return User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
        else:
            return user


    @staticmethod
    def extract(creator_name, project_name, archive_path):
        logger.debug("working directory", os.getcwd())
        logger.debug("path: %s", settings.MIRACLE_PROJECT_DIRECTORY)

        creator = Command.create_user(username=creator_name)
        project, created = Project.objects.get_or_create(name=project_name, creator=creator)

        logger.debug(archive_path)
        try:
            logger.debug("Extracting archive...")
            add_project(project, archive_path)
        except Exception as e:
            print e