from django.conf import settings

import logging
import os
import requests

logger = logging.getLogger(__name__)

DEFAULT_WORKING_DIRECTORY = getattr(settings, 'DEFAULT_WORKING_DIRECTORY_NAME', 'luxedemo')


def deployr_url(uri):
    return '{}/r/{}'.format(settings.DEPLOYR_URL, uri)


login_url = deployr_url('user/login')
create_working_directory_url = deployr_url('repository/directory/create')
upload_script_url = deployr_url('repository/file/upload')
execute_script_url = deployr_url('job/submit')


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


def run_script(script_file=None, workdir=DEFAULT_WORKING_DIRECTORY, parameters=None, user=None, job_name=None):
    if script_file is None or not os.path.isfile(script_file.name):
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
        'rscriptdirectory': workdir.DEFAULT_DEPLOYR_USER,
        'rscriptauthor': 'miracle',  # FIXME: hardcoded
    }
    if parameters:
        execute_script_data.update(inputs=parameters)
# submit job
    response = session.post(execute_script_url, data=execute_script_data)
    logger.debug("execute script response: %s", response.text)
    return response
