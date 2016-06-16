# Digging into Data: Mining relationships among variables in large datasets from complex systems
### Setup

We use [docker compose](https://docs.docker.com/compose/) to organize MIRACLE's components. These consist of Docker
images for the following:

* One container for a Django uWSGI application server, Celery, and Redis, all running under supervisord. We are
  aware that [Docker best practices](https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/) call
  for one process per container, but in the interests of expediency and limited development resources we've bundled
  these all together for the interim. If you'd like to help split them out, please send us a PR!
* One container for an nginx reverse proxy
* One container for a modified version of the [Radiant](https://github.com/vnijs/radiant) business analytics Shiny app
* One container for [DeployR](https://deployr.revolutionanalytics.com/) that provides our R script execution environment

### First steps

* [Install the latest version of docker-compose and docker](https://docs.docker.com/compose/install/) - currently 1.7.1
* Create a local user named 'miracle'. In order to handle file permissions on our shared volumes properly, make sure you
  create the user with a uid of 2000, or set the `MIRACLE\_UID` build argument before building the Docker images, e.g.,
  `MIRACLE_UID=2772 sh build.sh`
* add yourself to the docker group

### Local development

* Copy `development.yml` to `docker-compose.yml
* Copy and edit the Django settings files `cp django/miracle/settings/local.py.example django/miracle/settings/local.py` 
* Reload code in the uWSGI server via `touch django/miracle/deploy/uwsgi/miracle.ini` (lightweight) or `docker-compose restart miracle\_django\_1` (drastic)

### Production configuration and deployment

* Copy `production.yml` to `docker-compose.yml` and edit the relevant environment variables for the MIRACLE_ADMIN
* Copy SSL certs and private key into the nginx directory as `server.crt` and `server.key`, respectively
* Change all passwords, keys and secrets in `docker-compose.yml` and 
  - `docker-compose.yml`
  - `deployr/addUser.py`
  - `django/entrypoint.sh`
  - `django/miracle/settings/local.py`

### Build the images and spin up the docker containers

* Build the images and start the containers via `% sh build.sh`
* In the future, you can start everything up via `docker-compose up -d` and take them down via `docker-compose down`
* The `miracle` homepage should be live at `https://localhost` at this point

### Loading Data

You can load the `luxedemo.packrat.tar.gz` and `rhea.packrat.tar.gz` from the
[miracle example projects github repository](https://github.com/comses/miracle-example-projects) via the command line by
downloading the `packrat.tar.gz` files into the `django` directory (this project's source tree is mapped to
/code/ in the Django container by default) and performing the following steps:

```
% docker exec -it miracle_django_1 bash # login to the container
% cd django;
% ./manage.py load_project luxedemo.packrat.tar.gz --creator=<username> --project=luxedemo
% ./manage.py load_project rhea.packrat.tar.gz --creator=<username> --project=rhea
```

### Status
[![Build Status](https://travis-ci.org/comses/miracle.svg?branch=master)](https://travis-ci.org/comses/miracle)
[![Coverage Status](https://coveralls.io/repos/comses/miracle/badge.svg)](https://coveralls.io/r/comses/miracle)
[![Code Health](https://landscape.io/github/comses/miracle/master/landscape.svg?style=flat)](https://landscape.io/github/comses/miracle/master)

