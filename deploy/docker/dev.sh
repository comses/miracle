#!/usr/bin/env bash
/code/deploy/docker/wait-for-it.sh db:5432 -- python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --no-input -c
python manage.py initadmin
mkdir -p /miracle/logs/supervisor && chown $USERNAME: /miracle/logs/supervisor
/usr/bin/supervisord -u $USERNAME -c /code/deploy/supervisord/dev.conf
