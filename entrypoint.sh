#!/bin/sh

set -e
echo "$1"

if [ "$1" = 'dev' ]; then
    python manage.py collectstatic --no-input
    echo "static collected"
    wait-for postgres:5432 -- python manage.py migrate && python createsuperuser.py
    python manage.py runserver 0.0.0.0:8000
    fi

if [ "$1" = 'web' ]; then
    python manage.py collectstatic --no-input
    echo "static collected"
    wait-for postgres:5432 -- python manage.py migrate && python createsuperuser.py
    /usr/local/bin/gunicorn caaas.wsgi:application -w 2 -b :8000
    fi


