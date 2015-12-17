from __future__ import absolute_import
from django.core import files
from django.conf import settings
from miracle.core import deployr
from miracle.celery import app
from miracle.core.models import DataAnalysisScript, AnalysisOutput

from celery import chain

# Metadata Pipeline Imports
from . import archive_extractor
from . import filegrouper
from . import filegroup_extractors
from . import metadatagrouper
from . import metadatagroup_loaders

import json
import logging

logger = logging.getLogger(__name__)


@app.task(bind=True)
def run_analysis_task(self, analysis_id, parameters, user=None):
    if user is None:
        raise ValueError("Must pass in a Django User to execute analysis {}".format(user))
    logger.debug("user %s requesting script execution (%s) with parameters (type: %s) %s", user, analysis_id,
                 type(parameters), parameters)
    analysis = DataAnalysisScript.objects.get(pk=analysis_id)

    output = AnalysisOutput.objects.create(analysis=analysis, name=analysis.default_output_name, creator=user,
                                           parameter_values_json=parameters)
    deployr_input_parameters_dict = analysis.to_deployr_input_parameters(json.loads(parameters))
    self.update_state(state='PROCESSING')
    job = deployr.run_script(script_file=analysis.path.filepath, parameters=deployr_input_parameters_dict,
                             user=user, job_name='{}-{}'.format(analysis.name, output.pk))
    output.response = job.response.text
    output.save()
    self.update_state(state='RETRIEVING_OUTPUT',
                      meta={'response': output.response})
    results = job.retrieve_files()
    # results is a list of tuples (file, metadata)
    for result in results:
        temporary_file = result[0]
        metadata = result[1]
        logger.debug("creating analysis output file from [%s, %s]", temporary_file, metadata)
        with open(temporary_file, 'rb') as of:
            # metadata is a python dict at this point, still need to serialize it back to JSON before storing it
            analysis_output_file = output.files.create(metadata=json.dumps(metadata))
            analysis_output_file.output_file.save(metadata['filename'], files.File(of), save=True)
    self.update_state(state='COMPLETED',
                      meta={'output_id': output.pk})
    return output


@app.task()
def extract_archive(project, archive):
    return archive_extractor.extract(project, archive, settings.MIRACLE_PROJECT_DIRECTORY)


@app.task()
def group_files(project_file_paths):
    return filegrouper.group_files(project_file_paths)


@app.task()
def extract_metadata_groups(project_grouped_file_paths):
    return filegroup_extractors.extract_metadata_groups(project_grouped_file_paths)


@app.task()
def group_metadata(metadata_collection):
    return metadatagrouper.group_metadata(metadata_collection)


@app.task()
def load_project(grouped_metadata):
    return metadatagroup_loaders.load_project(grouped_metadata)


def run_metadata_pipeline(project, archive):
    return chain(extract_archive.s(project, archive),
                 group_files.s(),
                 extract_metadata_groups.s(),
                 group_metadata.s(),
                 load_project.s())
