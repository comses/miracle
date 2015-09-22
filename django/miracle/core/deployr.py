from django.conf import settings

import json
import logging
import os
import requests
import time

logger = logging.getLogger(__name__)

DEFAULT_WORKING_DIRECTORY = getattr(settings, 'DEFAULT_WORKING_DIRECTORY_NAME', 'luxedemo')


def deployr_url(uri):
    return '{}/r/{}'.format(settings.DEPLOYR_URL, uri)


def deployr_post_data(**kwargs):
    return dict(format='json', **kwargs)


login_url = deployr_url('user/login')
create_working_directory_url = deployr_url('repository/directory/create')
upload_script_url = deployr_url('repository/file/upload')
submit_job_url = deployr_url('job/submit')
job_status_url = deployr_url('job/query')
job_results_url = deployr_url('project/directory/list')


def login(user=None):
    auth_tuple = get_auth_tuple(user)
    s = requests.Session()
    r = s.post(login_url, data={'username': auth_tuple[0], 'password': auth_tuple[1], 'format': 'json'})
    logger.debug(r.text)
    return s


def get_auth_tuple(user=None):
    # FIXME: currently using a single sandbox user - at some point we may want to switch to 1:1 deployr user <-> miracle
    # users
    return (settings.DEFAULT_DEPLOYR_USER, settings.DEFAULT_DEPLOYR_PASSWORD)
    """
    if user is None:
        return (settings.DEFAULT_DEPLOYR_USER, settings.DEFAULT_DEPLOYR_PASSWORD)
    else:
            return (user.username, 'changeme')
    """


class Job(object):

    def __init__(self, session=None, user=None):
        if session is None:
            if user is None:
                raise ValueError("must provide an active session or user to login")
            session = login(user)
        self.session = session

    def post(self, url, data=None, **kwargs):
        if data is None:
            data = kwargs
        data.setdefault('format', 'json')
        return self.session.post(url, data=data)

    def submit(self, data):
        logger.debug("submitting job with payload %s", data)
        response = self.post(submit_job_url, data)
        self.submit_response_json = response.json()
        job_data = self.get_job_data(self.submit_response_json)
        self.job_id = job_data['job']
        self.submit_successful = self.submit_response_json['deployr']['response']['success']
        return response

    def check_status(self, wait=True, counter=0, limit=50, job_id=None):
        if job_id is None:
            job_id = getattr(self, 'job_id', None)
            if job_id is None:
                raise ValueError("Submit a job first or pass a valid job id into this method")

        response = self.post(job_status_url, job=job_id)
        response_json = response.json()
        if not self.is_job_completed(response_json):
            if wait and counter < limit:
                # recur up to the limit
                time.sleep(1000)
                self.check_status(wait, counter + 1, limit, job_id)
            return response
        else:
            self.project_id = self.get_project_id(response_json)
            # retrieve results
            response = self.post(job_results_url, project=self.project_id)
        return response

    def is_job_completed(self, response_json):
        return self.get_job_data(response_json)['status'] == 'Completed'

    def get_job_data(self, response_json):
        try:
            return response_json['deployr']['response']['job']
        except:
            raise ValueError("invalid json {}".format(response_json))

    def get_job_id(self, response_json):
        return self.get_job_data(response_json)['job']

    def get_project_id(self, response_json):
        return self.get_job_data(response_json)['project']


def run_script(script_file=None, workdir=DEFAULT_WORKING_DIRECTORY, parameters=None, user=None, job_name=None):
    if script_file is None or not os.path.isfile(script_file.path):
        raise ValueError("No script file to execute {}".format(script_file))
    if user is None:
        raise ValueError("No user found to execute file {}".format(script_file))
    if job_name is None:
        job_name = '{}.job'.format(workdir)

    logger.debug("user %s running script %s in working directory %s with parameters %s", user, script_file, workdir,
                 parameters)
    session = login(user)
    # parse and validate response
    # FIXME: figure out how to handle script scratch space / working directory allocation in deployr
    response = session.post(create_working_directory_url,
                            data={'format': 'json', 'directory': workdir})
    logger.debug("create working directory response: %s", response.text)
    filename = os.path.basename(script_file.name)
    response = session.post(upload_script_url,
                            files={'file': script_file},
                            data={'format': 'json',
                                  'filename': filename,
                                  'directory': workdir
                                  })
    logger.debug("upload script response: %s", response.text)
    execute_script_data = {
        'format': 'json',
        'name': job_name,
        'rscriptname': filename,
        'rscriptdirectory': workdir,
        'rscriptauthor': 'miracle',  # FIXME: hardcoded
    }
    if parameters:
        execute_script_data.update(inputs=json.loads(parameters))
    # submit job
    job = Job(session)
    job.submit(execute_script_data)
    return job
