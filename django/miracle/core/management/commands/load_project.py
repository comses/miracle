from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from ...extractors import Extractor, to_project_from_file
from ...models import User
import logging
import os, shutil

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Create an project from an uploaded archive.
    """
    help = 'Import a project'

    def add_arguments(self, parser):
        parser.add_argument('--overwrite-project',
                            dest='overwrite',
                            default=True,
                            help='Delete the project with the same name before adding the project')
        parser.add_argument('--creator',
                            nargs=1,
                            type=str,
                            help='The user created the project')
        parser.add_argument('--group-file',
                            nargs=1,
                            type=str,
                            help='A file that describes how to group the datatables into datasets')
        parser.add_argument('archive_file',
                            nargs=1,
                            type=str,
                            help='The archived project file you want to import')

    def handle(self, *args, **options):
        logger.debug(args)
        logger.debug(options)

        overwrite = options['overwrite']
        creator_name = options['creator'][0]
        archive_path = options['archive_file'][0]
        group_file = options['group_file'][0]

        logger.debug("path: %s", settings.MIRACLE_PROJECT_DIRECTORY)

        creator = User.objects.get(username=creator_name)

        logger.debug(archive_path)
        try:
            logger.debug("Extracting archive...")
            extractor = Extractor.from_archive(archive_path, overwrite=overwrite)
            metadata = extractor.metadata
            to_project_from_file(metadata, group_file, creator)
            self.stdout.write("Successfully imported data")
        except Exception as e:
            print e