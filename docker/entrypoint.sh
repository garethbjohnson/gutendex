#!/bin/bash

set -e

if [ "$1" = 'dev' ]; then
    python manage.py collectstatic --no-input
    echo "static collected"
    sleep 5
    python manage.py migrate && python createsuperuser.py
    if [ "$2" = true ]; then
        python manage.py updatecatalog > /dev/null 2>&1 &
        fi
    python manage.py runserver 0.0.0.0:8000
    fi

if [ "$1" = 'web' ]; then
    python manage.py collectstatic --no-input
    echo "static collected"
    python manage.py migrate && python createsuperuser.py
    if [ "$2" = true ]; then
        python manage.py updatecatalog > /dev/null 2>&1 &
        fi
    /usr/local/bin/gunicorn gutendex.wsgi:application -w 2 -b :8000
    fi


