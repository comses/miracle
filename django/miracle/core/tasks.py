from __future__ import absolute_import
from django.core import files
from miracle.core import deployr
from miracle.celery import app
from miracle.core.models import Analysis, AnalysisOutput

import json
import logging

logger = logging.getLogger(__name__)


@app.task
def run_analysis_task(analysis_id, parameters, user=None):
    if user is None:
        raise ValueError("Must pass in a Django User to execute analysis {}".format(user))
    logger.debug("user %s requesting script execution (%s) with parameters %s", user, analysis_id, parameters)
    analysis = Analysis.objects.get(pk=analysis_id)
    output = AnalysisOutput.objects.create(analysis=analysis, name='Demo Analysis Output', creator=user,
                                           parameter_values_json=parameters)
    job = deployr.run_script(script_file=analysis.uploaded_file, parameters=parameters, user=user,
                             job_name='{}-{}'.format(analysis.name, output.pk))
    output.response = job.response.text
    output.save()
    results = job.retrieve_files()
# results is a list of tuples (file, metadata)
    for result in results:
        metadata = result[1]
        with open(result[0], 'rb') as of:
            # metadata is a python dict at this point, still need to serialize it back to JSON before storing it
            aof = output.files.create(metadata=json.dumps(metadata))
            aof.output_file.save(metadata['filename'], files.File(of))
