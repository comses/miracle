from django.core.management.base import BaseCommand
from django.conf import settings
from miracle.core.tasks import run_metadata_pipeline
from miracle.core.models import Project, User
import logging
import os
import sys
import getpass

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Create an project from an uploaded archive.
    """
    help = 'Import a project'

    def add_arguments(self, parser):
        parser.add_argument('--creator',
                            default=os.environ.get('MIRACLE_USER'),
                            help='Django username for the creator of the project')
        parser.add_argument('--project',
                            help='The shortname of the project')
        parser.add_argument('archive_file',
                            help='''Path to an archived project file to be imported. This file must have a filesystem
                            structure that conforms to the guidelines listed at
                            https://github.com/comses/miracle/wiki/Project-Archive-Preparation-Guidelines''',
                            )

    def handle(self, *args, **options):
        logger.debug(args)
        logger.debug(options)
        creator_name = options['creator']
        project_shortname = options['project']
        archive_path = options['archive_file']

        self.extract(creator_name, project_shortname, archive_path)

    @staticmethod
    def create_user(username='testuser', email='miracle-test@mailinator.com',
                    first_name='Default', last_name='Testuser'):
        user_exists = User.objects.filter(username=username).exists()
        if not user_exists:
            sys.stdout.write("User {} does not exist yet\n".format(username))
            password = getpass.getpass("Enter a password for {}: ".format(username))
            return User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
        else:
            user = User.objects.get(username=username)
            return user

    @staticmethod
    def extract(creator_name, project_shortname, archive_path):
        abs_archive_path = os.path.abspath(archive_path)
        logger.debug("Extracting archive: {}".format(abs_archive_path))
        logger.debug("Working Directory: {}".format(os.getcwd()))
        logger.debug("project path: %s", settings.MIRACLE_PROJECT_DIRECTORY)

        creator = Command.create_user(username=creator_name)
        project, created = Project.objects.get_or_create(name=project_shortname, slug=project_shortname, creator=creator)

        logger.debug(archive_path)
        try:
            res = run_metadata_pipeline(project, archive_path, delete_archive_on_failure=False)
            logger.debug("Extraction succeeded for archive at %s", abs_archive_path)
        except Exception:
            logger.exception("Extraction failed for archive %s", abs_archive_path)
