from __future__ import absolute_import
from django.core import files
from miracle.core import deployr
from miracle.celery import app
from miracle.core.models import DataAnalysisScript, AnalysisOutput
from miracle.core.metadata_interface import add_project, associate_metadata_with_file

import json
import logging

logger = logging.getLogger(__name__)


@app.task(bind=True)
def run_analysis_task(self, analysis_id, parameters, user=None):
    if user is None:
        raise ValueError("Must pass in a Django User to execute analysis {}".format(user))
    logger.debug("user %s requesting script execution (%s) with parameters (type: %s) %s", user, analysis_id, type(parameters), parameters)
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


@app.task(bind=True)
def add_project_task(self, project, archive, projects_folder):
    return add_project(project, archive, projects_folder)
