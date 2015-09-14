from __future__ import absolute_import
from django.conf import settings
from miracle.core import deployr
from miracle.celery import app
from miracle.core.models import Analysis

import logging

logger = logging.getLogger(__name__)

@app.task
def run_analysis_task(analysis_id, parameters):
    logger.debug("running script: %s with parameters %s", analysis_id, parameters)
    analysis = Analysis.objects.get(pk=analysis_id)
    deployr.run_script(analysis, parameters)
