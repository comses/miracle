#!/usr/bin/env bash
sleep 10
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py initadmin
mkdir -p /miracle/logs/supervisor
/usr/bin/supervisord -c /code/django/deploy/supervisord/supervisord.conf
