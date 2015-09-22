from __future__ import absolute_import
from miracle.core import deployr
from miracle.celery import app
from miracle.core.models import Analysis, AnalysisOutput

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
    response = deployr.run_script(script_file=analysis.uploaded_file, parameters=parameters, user=user,
                                  job_name='{}-{}'.format(analysis.name, output.pk))
    output.response = response.text
    output.save()
