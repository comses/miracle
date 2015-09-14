from __future__ import absolute_import
from django.conf import settings
from miracle.core import deployr
from miracle.celery import app

import logging

logger = logging.getLogger(__name__)

@app.task
def run_analysis(analysis_id, parameters):
    logger.debug("running script: %s with parameters %s", analysis_id, parameters)
    deployr.run_script(analysis_id, parameters)
