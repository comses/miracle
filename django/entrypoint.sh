#!/usr/bin/env bash

init() {
    python manage.py makemigrations
    python manage.py migrate    
    python manage.py shell <<EOF
import os
from miracle.core.models import User

User.objects.create_user(username=os.environ['MIRACLE_USER'],
                         password=os.environ['MIRACLE_PASS'],
                         email=os.environ['MIRACLE_EMAIL'])
EOF
}

rundev() {
    init
    python manage.py runserver 0.0.0.0:8000
}

runprod() {
    init
    uwsgi --ini deploy/uwsgi/miracle.ini
}

case "$1" in
    dev)  rundev;;
    prod) runprod;;
    *) "$@";;
esac
