from subprocess import call
import json
import os
import shutil
from time import strftime
import sys
import urllib.request
import tarfile
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from books import utils
from books.models import *


TEMP_PATH = settings.CATALOG_TEMP_DIR

URL = 'https://gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2'
DOWNLOAD_PATH = os.path.join(TEMP_PATH, 'catalog.tar.bz2')


LOG_DIRECTORY = settings.CATALOG_LOG_DIR
LOG_FILE_NAME = strftime('%Y-%m-%d_%H%M%S') + '.txt'
LOG_PATH = os.path.join(LOG_DIRECTORY, LOG_FILE_NAME)


def log(*args):
    print(*args)
    if not os.path.exists(LOG_DIRECTORY):
        os.makedirs(LOG_DIRECTORY)
    with open(LOG_PATH, 'a') as log_file:
        text = ' '.join(args) + '\n'
        log_file.write(text)


def get_id(filepath):
    id = filepath.split('/')[2]
    try:
        id = int(id)
    except ValueError:
        id = None
    return id


def put_catalog_in_db(tar):
    c = 0
    id_in_file = set()
    for file in tar:
        if c <= 80:
            c += 1
            f = tar.extractfile(file)
            id = get_id(file.name)
            id_in_file.add(id)
            # creates a string of the xml
            content = f.read().decode('utf-8')
            if (c % 500 == 0):
                log(f'{c} books loaded')

            book = utils.get_book(id, content)
            try:
                ''' Make/update the book. '''

                book_in_db = Book.objects.get_or_create(gutenberg_id=id,
                                                copyright=book['copyright'],
                                                download_count=book['downloads'],
                                                media_type=book['type'],
                                                title=book['title']
                                                )[0]

                ''' Make/update the authors. '''

                book_in_db.authors.clear()
                for author in book['authors']:
                    person = Person.objects.get_or_create(
                        name=author['name'],
                        birth_year=author['birth'],
                        death_year=author['death']
                    )[0].id
                    book_in_db.authors.add(person)

                ''' Make/update the translators. '''
                book_in_db.translators.clear()
                for translator in book['translators']:
                    person = Person.objects.get_or_create(
                        name=translator['name'],
                        birth_year=translator['birth'],
                        death_year=translator['death']
                    )[0].id
                    book_in_db.translators.add(person)

                ''' Make/update the book shelves. '''

                book_in_db.bookshelves.clear()
                for shelf in book['bookshelves']:
                    shelf_in_db = Bookshelf.objects.get_or_create(name=shelf)[0].id
                    book_in_db.bookshelves.add(shelf_in_db)

                ''' Make/update the formats. '''

                old_formats = Format.objects.filter(book=book_in_db)

                format_ids = []
                for format_ in book['formats']:
                    format_in_db = Format.objects.get_or_create(
                        book=book_in_db,
                        mime_type=format_,
                        url=book['formats'][format_]
                    )[0].id
                    format_ids.append(format_in_db)

                for old_format in old_formats:
                    if old_format.id not in format_ids:
                        old_format.delete()

                ''' Make/update the languages. '''
                book_in_db.languages.clear()
                for language in book['languages']:
                    language_in_db = Language.objects.get_or_create(code=language)[0].id
                    book_in_db.languages.add(language_in_db)

                ''' Make/update subjects. '''

                book_in_db.subjects.clear()
                for subject in book['subjects']:
                    subject_in_db = Subject.objects.get_or_create(name=subject)[0].id
                    book_in_db.subjects.add(subject_in_db)

            except Exception as error:
                book_json = json.dumps(book, indent=4)
                log(
                    '  Error while putting this book info in the database:\n',
                    book_json,
                    '\n'
                )
                raise error
            
    return id_in_file


def send_log_email():
    if not (settings.ADMIN_EMAILS or settings.EMAIL_HOST_ADDRESS):
        return

    log_text = ''
    with open(LOG_PATH, 'r') as log_file:
        log_text = log_file.read()

    email_html = '''
        <h1 style="color: #333;
                   font-family: 'Helvetica Neue', sans-serif;
                   font-size: 64px;
                   font-weight: 100;
                   text-align: center;">
            Gutendex
        </h1>

        <p style="color: #333;
                  font-family: 'Helvetica Neue', sans-serif;
                  font-size: 24px;
                  font-weight: 200;">
            Here is the log from your catalog retrieval:
        </p>

        <pre style="color:#333;
                    font-family: monospace;
                    font-size: 16px;
                    margin-left: 32px">''' + log_text + '</pre>'

    email_text = '''GUTENDEX

    Here is the log from your catalog retrieval:

    ''' + log_text

    send_mail(
        subject='Catalog retrieval',
        message=email_text,
        html_message=email_html,
        from_email=settings.EMAIL_HOST_ADDRESS,
        recipient_list=settings.ADMIN_EMAILS
    )
# todo
def detect_stale_entries(id_in_file):
    log('  Detecting stale directories...')
    qs = Book.objects.exclude(Q(gutenberg_id__in=id_in_file) | Q(gutenberg_id__isnull=True))
    log('  Removing stale directories and books...')
    for book in qs:
        log(f"removing {book.title}")
        book.delete()


class Command(BaseCommand):
    help = 'This replaces the catalog files with the latest ones.'

    def handle(self, *args, **options):
        # try:
        date_and_time = strftime('%H:%M:%S on %B %d, %Y')
        log('Starting script at', date_and_time)

        log('  Making temporary directory...')
        os.makedirs(TEMP_PATH, exist_ok=True)

        log('  Downloading compressed catalog...')
        urllib.request.urlretrieve(URL, DOWNLOAD_PATH)

        log('  Reading catalog...')

        tar = tarfile.open(DOWNLOAD_PATH, 'r:bz2')

        log('  Putting the catalog in the database...')
        id_in_file = put_catalog_in_db(tar)
        print(id_in_file)
        detect_stale_entries(id_in_file)
        log('  Removing temporary files...')
        shutil.rmtree(TEMP_PATH)

        log('Done!\n')
        # except Exception as error:
        #     error_message = str(error)
        #     log('Error:', error_message)
        #     log('')
        #     shutil.rmtree(TEMP_PATH)

        # # send_log_email()
