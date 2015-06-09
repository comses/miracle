from fabric.api import local, sudo, cd, env, execute, roles, task, run
from fabric.context_managers import prefix
from fabric.contrib.console import confirm
from fabric.contrib import django
import sys
import os
import logging

logger = logging.getLogger(__name__)

# default to current working directory
env.project_path = os.path.dirname(__file__)
# needed to push catalog.settings onto the path.
env.abs_project_path = os.path.abspath(env.project_path)
sys.path.append(env.abs_project_path)

# default env configuration
env.roledefs = {
    'localhost': ['localhost'],
    'staging': ['staging.server'],
    'prod': ['production.server'],
}
env.python = 'python'
env.project_name = 'miracle'
env.project_conf = 'miracle.settings'
env.deploy_user = 'miracle'
env.deploy_group = 'comses'
env.db_user = 'miracle'
env.databases = ('miracle_metadata', 'miracle_data')
env.deploy_parent_dir = '/opt/'
env.git_url = 'https://github.com/comses/miracle.git'
env.services = 'nginx redis supervisord'
env.docs_path = os.path.join(env.project_path, 'docs')
env.virtualenv_path = '%s/.virtualenvs/%s' % (os.getenv('HOME'), env.project_name)
env.ignored_coverage = ('test', 'settings', 'migrations', 'fabfile', 'wsgi',)
env.solr_conf_dir = '/etc/solr/conf'
env.vcs = 'git'
env.vcs_command = 'export GIT_WORK_TREE=%(deploy_dir)s && git checkout -f %(branch)s && git pull'

# django integration for access to settings, etc.
django.project(env.project_name)
from django.conf import settings as miracle_settings


@task
def clean_update():
    local("git fetch --all && git reset --hard origin/master")


@task(alias='sh')
def shell_plus():
    dj('shell_plus')


def dj(command, **kwargs):
    """
    Shortcut for running a django manage.py command
    """
    _virtualenv(local,
                'python manage.py {dj_command} --settings {project_conf}'.format(dj_command=command, **env), **kwargs)


def _virtualenv(executor, *commands, **kwargs):
    """ Executes a command inside the virtualenv """
    command = ' && '.join(commands)
    with prefix('. %(virtualenv_path)s/bin/activate' % env):
        executor(command, **kwargs)


@task
def host_type():
    run('uname -a')


@roles('localhost')
@task(alias='cov')
def coverage():
    execute(test, coverage=True)
    ignored = ['*{0}*'.format(ignored_pkg) for ignored_pkg in env.ignored_coverage]
    local('coverage html --omit=' + ','.join(ignored))


@roles('localhost')
@task(alias='te')
def test(name=None, coverage=False):
    if name is not None:
        env.apps = name
    else:
        env.apps = ' '.join(miracle_settings.MIRACLE_APPS)
    if coverage:
        ignored = ['*{0}*'.format(ignored_pkg) for ignored_pkg in env.ignored_coverage]
        env.python = "coverage run --source='.' --omit=" + ','.join(ignored)
    local('%(python)s manage.py test %(apps)s' % env)


@task(alias='ser')
def server(ip="127.0.0.1", port=8000):
    """
    Starts the Django development server. To bind to an external IP, run via `fab server:ip=your.external.ip`
    """
    dj('runserver {ip}:{port}'.format(ip=ip, port=port), capture=False)


@roles('staging')
@task(alias='dev')
def staging():
    execute(deploy, 'develop')


@roles('prod')
@task
def prod():
    execute(deploy, 'master')


@roles('localhost')
@task
def setup():
    execute(setup_postgres)
    execute(initialize_database_schema)


@roles('localhost')
@task(alias='ri')
def index():
    local('python manage.py rebuild_index')


@roles('localhost')
@task
def setup_postgres():
    local("createuser %(db_user)s -e --createdb -U postgres" % env)
    for db in env.databases:
        local("createdb {0} -U {1}".format(db, env.db_user))


@task(aliases=['idb', 'initdb'])
def initialize_database_schema():
    """
    Creates the Django DB schema by running makemigrations and then a migrate.
    """
    local('python manage.py makemigrations')
    local('python manage.py migrate')


@roles('localhost')
@task(alias='rebs')
def rebuild_schema():
    if confirm("Delete existing db schemas and rerun migrations? All data in {} will be lost.".format(env.databases)):
        for db in env.databases:
            local("dropdb --if-exists {0} -U {1} && createdb {0} -U {1}".format(db, env.db_user))
        local("find . -name '00*.py' -print -delete")
        execute(initialize_database_schema)


def _restart_command(systemd=True):
    """
    Returns a systemctl or SysV system restart command for the services defined in env.services
    """
    if systemd:
        cmd = 'systemctl restart %(services)s && systemctl status -l %(services)s'
    else:
        cmd = ' && '.join(['service %s restart' % service for service in env.services.split()])
    return cmd % env


@roles('localhost')
@task
def clean():
    with cd(env.project_path):
        sudo('find . -name "*.pyc" -delete -print')
        sudo('rm -rvf htmlcov')
        sudo('rm -rvf docs/build')


@task
def restart():
    sudo(_restart_command(), pty=True)


def sudo_chain(*commands, **kwargs):
    sudo(' && '.join(commands), **kwargs)


def deploy(branch):
    """ deploy to an already setup environment """
    env.deploy_dir = env.deploy_parent_dir + env.project_name
    env.branch = branch
    if confirm("Deploying '%(branch)s' branch to host %(host)s : \n\r%(vcs_command)s\nContinue? " % env):
        with cd(env.deploy_dir):
            sudo_chain(
                env.vcs_command,
                'chmod g+s logs',
                'chmod -R g+rw logs/',
                user=env.deploy_user, pty=True)
            env.static_root = miracle_settings.STATIC_ROOT
            if confirm("Update pip dependencies?"):
                _virtualenv(sudo, 'pip install -Ur requirements.txt', user=env.deploy_user)
            if confirm("Run database migrations?"):
                _virtualenv(sudo, '%(python)s manage.py migrate' % env, user=env.deploy_user)
            _virtualenv(sudo, '%(python)s manage.py collectstatic' % env)
            sudo_chain(
                'chmod -R ug+rw .',
                'find %(static_root)s %(virtualenv_path)s -type d -exec chmod a+x {} \;' % env,
                'find %(static_root)s %(virtualenv_path)s -type f -exec chmod a+r {} \;' % env,
                'find . -type d -exec chmod ug+x {} \;',
                'chown -R %(deploy_user)s:%(deploy_group)s . %(static_root)s %(virtualenv_path)s' % env,
                _restart_command(),
                pty=True)
