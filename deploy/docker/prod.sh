#!/bin/sh
/code/deploy/docker/wait-for-it.sh db:5432 -- python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py initadmin
mkdir -p /miracle/logs/supervisor
crond
/usr/bin/supervisord -u $USERNAME -c /code/deploy/supervisord/prod.conf
