#!/usr/bin/env bash
sleep 10
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py initadmin
/usr/bin/supervisord -c /code/deploy/supervisord/supervisord.conf
