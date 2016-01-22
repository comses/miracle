from __future__ import absolute_import

from django.core import files
from django.conf import settings
from celery import chain

from miracle.celery import app
from . import deployr
from .models import DataAnalysisScript, AnalysisOutput, ParameterValue, AnalysisParameter

import os

# Metadata Pipeline Imports
from .ingest import pipeline

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

    output = AnalysisOutput.objects.create(analysis=analysis, name=analysis.default_output_name, creator=user)
    for parameter in parameters:
        analysis_parameter = AnalysisParameter.objects.get(id=parameter['id'])
        ParameterValue.objects.create(parameter=analysis_parameter, output=output, value=parameter['value'])
    deployr_input_parameters_dict = analysis.to_deployr_input_parameters(parameters)
    self.update_state(state='PROCESSING')
    job = deployr.run_script(script_name=analysis.basename, parameters=deployr_input_parameters_dict,
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
        with open(temporary_file, 'rb') as output_file:
            # metadata is a python dict at this point, still need to serialize it back to JSON before storing it
            analysis_output_file = output.files.create(metadata=json.dumps(metadata))
            analysis_output_file.output_file.save(metadata['filename'], files.File(output_file), save=True)
    self.update_state(state='COMPLETED',
                      meta={'output_id': output.pk})
    return output


@app.task(bind=True)
def run_metadata_pipeline(self, project, archive):
    logger.debug("running metadata pipeline for project %s on archive %s", project, archive)
    return pipeline.run(project, archive)
