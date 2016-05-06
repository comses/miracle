#!/usr/bin/env bash
sleep 10
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
echo "import os; from django.contrib.auth.models import User; User.objects.create_superuser(os.environ['MIRACLE_USER'], os.environ['MIRACLE_EMAIL'], 'changeme_django') if not User.objects.filter(username=os.environ['MIRACLE_USER']).exists() else None;" | python manage.py shell
/usr/bin/supervisord

