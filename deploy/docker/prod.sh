#!/bin/sh
/code/deploy/docker/wait-for-it.sh db:5432 -- python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py initadmin
crond
chown -R $USERNAME: /miracle
/usr/bin/supervisord -u $USERNAME -c /code/deploy/supervisord/prod.conf
