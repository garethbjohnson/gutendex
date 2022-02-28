#!/bin/bash

set -e
echo "$1"

if [ "$1" = 'dev' ]; then
    python manage.py collectstatic --no-input
    echo "static collected"
    sleep 5
    python manage.py migrate && python createsuperuser.py
    python manage.py runserver 0.0.0.0:8000
    fi

if [ "$1" = 'web' ]; then
    python manage.py collectstatic --no-input
    echo "static collected"
    python manage.py migrate && python createsuperuser.py
    /usr/local/bin/gunicorn gutendex.wsgi:application -w 2 -b :8000
    fi


