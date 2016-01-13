from django.conf import settings

import json
import logging
import os
import requests
import tempfile
import time

logger = logging.getLogger(__name__)

DEFAULT_WORKING_DIRECTORY = getattr(settings, 'DEFAULT_WORKING_DIRECTORY_NAME', 'luxedemo')


def deployr_url(uri):
    return '{}/r/{}'.format(settings.DEPLOYR_URL, uri)


login_url = deployr_url('user/login')
create_working_directory_url = deployr_url('repository/directory/create')
upload_script_url = deployr_url('repository/file/upload')
submit_job_url = deployr_url('job/submit')
job_status_url = deployr_url('job/query')
job_results_url = deployr_url('project/directory/list')


def response200orError(response):
    if response.status_code != 200:
        error = DeployrUnexpectedStatusCode(response)
        logger.exception(error)
        raise error


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


def login(user=None):
    auth_tuple = get_auth_tuple(user)
    s = requests.Session()
    r = s.post(login_url, data={'username': auth_tuple[0], 'password': auth_tuple[1], 'format': 'json'})
    response200orError(r)
    logger.debug("LOGIN response: %s" % r.text)
    return s


class DeployrUnexpectedStatusCode(Exception):
    pass


class DeployrAPI(object):
    """
    Add projects and scripts to deployr
    """

    @staticmethod
    def create_working_directory(name, session):
        response = session.post(create_working_directory_url,
                                data={'format': 'json', 'directory': name})
        logger.debug("CREATE WORKING DIRECTORY response: %s", response.text)
        return response

    @staticmethod
    def upload_script(script_path, project_name, session):
        base_script_path = os.path.basename(script_path)
        response = session.post(upload_script_url,
                                files={'file': open(script_path, 'rb')},
                                data={'format': 'json',
                                      'filename': base_script_path,
                                      'directory': project_name
                                      })
        logger.debug("UPLOAD SCRIPT response: %s", response.text)
        return response

    @staticmethod
    def run_job(script_path, project_name, parameters, session):
        job_name = '{}.job'.format(project_name)
        execute_script_data = {
            'format': 'json',
            'name': job_name,
            'rscriptname': script_path,
            'rscriptdirectory': project_name,
            'rscriptauthor': settings.DEFAULT_DEPLOYR_USER,
        }
        if parameters:
            # Convert parameters dict to be JSON-encoded
            execute_script_data.update(inputs=json.dumps(parameters))
        job = Job(session)
        job.submit(execute_script_data)
        logger.debug("JOB SUBMITTED: %s" % job_name)
        return job

    @staticmethod
    def check_job_status(job):
        (response, completed) = job.check_status()
        logger.debug("RUN SCRIPT successful? [{}] response: {}".format(completed, response.text))
        return (response, completed)


class Job(object):
    def __init__(self, session=None, user=None):
        if session is None:
            if user is None:
                raise ValueError("must provide an active session or user to login")
            session = login(user)
        self.session = session

    def get(self, url, **kwargs):
        return self.session.get(url, **kwargs)

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

    def check_status(self, retry=True, counter=0, limit=30, job_id=None):
        if job_id is None:
            job_id = getattr(self, 'job_id', None)
            if job_id is None:
                raise ValueError("Submit a job first or pass a valid job id into this method")

        logger.debug("checking status of job %s with counter %s", job_id, counter)
        response = self.post(job_status_url, job=job_id)
        response_json = response.json()
        completed = self.is_job_completed(response_json)
        logger.debug("job was completed? %s with response %s", completed, response.text)
        if not completed:
            logger.debug("job wasn't completed, trying again in 10 seconds.")
            if retry and counter < limit:
                # recur up to the limit
                time.sleep(10)
                logger.debug("done sleeping, about to retry")
                return self.check_status(retry, counter=counter + 1, limit=limit, job_id=job_id)
            else:
                logger.debug("job took too long to complete - aborting")
        else:
            self.project_id = self.get_project_id(response_json)
            logger.debug("project id %s", self.project_id)
            # retrieve results
            response = self.post(job_results_url, project=self.project_id)
            logger.debug("results response: %s", response.text)
            self.results = self.get_results(response.json())
            logger.debug("results: %s", self.results)
        self.response = response
        self.completed = completed
        return (response, completed)

    def get_results(self, response_json):
        return response_json['deployr']['response']['directory']['files']

    def retrieve_files(self):
        """
        Returns a list of (File, JSON metadata about the file) tuples.
        """
        results = getattr(self, 'results', None)
        if results is None or not self.completed:
            raise ValueError("No results available, try running check_status again.")
        files = []
        temp_directory = tempfile.mkdtemp(prefix=self.project_id)
        for result in results:
            url = result['url']
            filename = result['filename']
            response = self.get(url, stream=True)
            if not response.ok:
                logger.error("unable to retrieve file %s at url %s.\nResponse: %s", filename, url, response)
                continue
            result_file = os.path.join(temp_directory, filename)
            with open(result_file, 'wb') as f:
                for block in response.iter_content(1024):
                    f.write(block)
                files.append((f.name, result))
        return files

    def is_job_completed(self, response_json):
        return self.get_job_data(response_json)['status'] == 'Completed'

    def get_job_data(self, response_json):
        try:
            return response_json['deployr']['response']['job']
        except KeyError as e:
            raise ValueError("invalid json {}: {}".format(response_json, e))

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
    with login(user) as session:
        # FIXME: encapsulate this logic into Job or another class.
        response = session.post(create_working_directory_url,
                                data={'format': 'json', 'directory': workdir})
        # FIXME: parse and validate response
        logger.debug("CREATE WORKING DIRECTORY response: %s", response.text)
        filename = os.path.basename(script_file.name)
        response = session.post(upload_script_url,
                                files={'file': script_file},
                                data={'format': 'json',
                                      'filename': filename,
                                      'directory': workdir
                                      })
        # FIXME: parse and validate response
        logger.debug("UPLOAD SCRIPT response: %s", response.text)
        execute_script_data = {
            'format': 'json',
            'name': job_name,
            'rscriptname': filename,
            'rscriptdirectory': workdir,
            'rscriptauthor': 'miracle',  # FIXME: hardcoded
        }
        if parameters:
            # Convert parameters dict to be JSON-encoded
            execute_script_data.update(inputs=json.dumps(parameters))
        # submit job
        job = Job(session)
        job.submit(execute_script_data)
        time.sleep(15)
        (response, completed) = job.check_status()
        logger.debug("RUN SCRIPT successful? [{}] response: {}".format(completed, response.text))
        return job
