from django.core.management import call_command
from django.contrib.auth.management.commands.createsuperuser import get_user_model
import django
import os

DEBUG = os.getenv('DEBUG', 'NO').lower() in ('on', 'true', 'y', 'yes')
os.environ['DJANGO_SETTINGS_MODULE'] = 'gutendex.settings'


django.setup()


DJANGO_DB_NAME = os.environ.get('DJANGO_DB_NAME')
DJANGO_SU_NAME = os.environ.get('DJANGO_SU_NAME')
DJANGO_SU_EMAIL = os.environ.get('DJANGO_SU_EMAIL')
DJANGO_SU_PASSWORD = os.environ.get('DJANGO_SU_PASSWORD')


if get_user_model().objects.count() != 0:
    pass
else:
    get_user_model()._default_manager.db_manager(DJANGO_DB_NAME).create_superuser(
        username=DJANGO_SU_NAME, email=DJANGO_SU_EMAIL, password=DJANGO_SU_PASSWORD)