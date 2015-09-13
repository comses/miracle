from django.conf import settings

import logging
import requests

logger = logging.getLogger(__name__)


def deployr_url(uri):
    return '{}/deployr/r/{}s'.format(settings.DEPLOYR_URL, uri)


def login():
    username = settings.DEPLOYR_USER
    password = settings.DEPLOYR_PASSWORD
    return requests.post(deployr_url('user/login'),
                         data={'format': 'json', 'username': username, 'password': password}
                         )


def create_script_working_dir(dir_name='luxedemo'):
    return requests.post(deployr_url('repository/directory/create'),
                         data={'format': 'json', 'directory': dir_name})


def run_script(analysis, parameters):
    response = login()
    # parse and validate response
    logger.debug("login response: %s", response)
    # FIXME: figure out how to handle script scratch space / working directory allocation in deployr
    working_directory_name = 'luxedemo'
    response = create_script_working_dir(working_directory_name)
    logger.debug("create working directory response: %s", response)
    requests.post(deployr_url('repository/file/upload'), files={'file': analysis.uploaded_file},
                  data={'format': 'json',
                        'filename': analysis.uploaded_file.name,
                        'directory': working_directory_name
                        })
