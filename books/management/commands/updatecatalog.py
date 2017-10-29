from subprocess import call
import json
import os
import shutil
from time import strftime
import sys
import urllib.request

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError

from books import utils
from books.models import *


TEMP_PATH = settings.CATALOG_TEMP_DIR

URL = 'http://gutenberg.readingroo.ms/cache/generated/feeds/rdf-files.tar.bz2'
DOWNLOAD_PATH = os.path.join(TEMP_PATH, 'catalog.tar.bz2')

MOVE_SOURCE_PATH = os.path.join(TEMP_PATH, 'cache/epub')
MOVE_TARGET_PATH = settings.CATALOG_RDF_DIR

LOG_DIRECTORY = settings.CATALOG_LOG_DIR
LOG_FILE_NAME = strftime('%Y-%m-%d_%H%M%S') + '.txt'
LOG_PATH = os.path.join(LOG_DIRECTORY, LOG_FILE_NAME)


# This gives a set of the names of the subdirectories in the given file path.
def get_directory_set(path):
    directory_set = set()
    for directory_item in os.listdir(path):
        item_path = os.path.join(path, directory_item)
        if os.path.isdir(item_path):
            directory_set.add(directory_item)
    return directory_set


def log(*args):
    print(*args)
    if not os.path.exists(LOG_DIRECTORY):
        os.makedirs(LOG_DIRECTORY)
    with open(LOG_PATH, 'a') as log_file:
        text = ' '.join(args) + '\n'
        log_file.write(text)


def put_catalog_in_db():
    book_ids = []
    for directory_item in os.listdir(settings.CATALOG_RDF_DIR):
        item_path = os.path.join(settings.CATALOG_RDF_DIR, directory_item)
        if os.path.isdir(item_path):
            try:
                book_id = int(directory_item)
            except ValueError:
                # Ignore the item if it's not a book ID number.
                pass
            else:
                book_ids.append(book_id)
    book_ids.sort()
    book_directories = [str(id) for id in book_ids]

    for directory in book_directories:
        id = int(directory)

        if (id > 0) and (id % 500 == 0):
            log('    %d' % id)

        book_path = os.path.join(
            settings.CATALOG_RDF_DIR,
            directory,
            'pg' + directory + '.rdf'
        )

        book = utils.get_book(id, book_path)

        try:
            ''' Make/update the book. '''

            book_in_db = Book.objects.filter(gutenberg_id=id)

            if book_in_db.exists():
                book_in_db = book_in_db[0]
                book_in_db.download_count = book['downloads']
                book_in_db.media_type = book['type']
                book_in_db.title = book['title']
                book_in_db.save()
            else:
                book_in_db = Book.objects.create(
                    gutenberg_id=id,
                    download_count=book['downloads'],
                    media_type=book['type'],
                    title=book['title']
                )

            ''' Make/update the authors. '''

            authors = []
            for author in book['authors']:
                author_in_db = Author.objects.filter(
                    name=author['name'],
                    birth_year=author['birth'],
                    death_year=author['death']
                )
                if author_in_db.exists():
                    author_in_db = author_in_db[0]
                else:
                    author_in_db = Author.objects.create(
                        name=author['name'],
                        birth_year=author['birth'],
                        death_year=author['death']
                    )
                authors.append(author_in_db)

            book_in_db.authors.clear()
            for author in authors:
                book_in_db.authors.add(author)

            ''' Make/update the book shelves. '''

            bookshelves = []
            for shelf in book['bookshelves']:
                shelf_in_db = Bookshelf.objects.filter(name=shelf)
                if shelf_in_db.exists():
                    shelf_in_db = shelf_in_db[0]
                else:
                    shelf_in_db = Bookshelf.objects.create(name=shelf)
                bookshelves.append(shelf_in_db)

            book_in_db.bookshelves.clear()
            for bookshelf in bookshelves:
                book_in_db.bookshelves.add(bookshelf)

            ''' Make/update the formats. '''

            old_formats = Format.objects.filter(book=book_in_db)

            format_ids = []
            for format_ in book['formats']:
                format_in_db = Format.objects.filter(
                    book=book_in_db,
                    mime_type=format_,
                    url=book['formats'][format_]
                )
                if format_in_db.exists():
                    format_in_db = format_in_db[0]
                else:
                    format_in_db = Format.objects.create(
                        book=book_in_db,
                        mime_type=format_,
                        url=book['formats'][format_]
                    )
                format_ids.append(format_in_db.id)

            for old_format in old_formats:
                if old_format.id not in format_ids:
                    old_format.delete()

            ''' Make/update the languages. '''

            languages = []
            for language in book['languages']:
                language_in_db = Language.objects.filter(code=language)
                if language_in_db.exists():
                    language_in_db = language_in_db[0]
                else:
                    language_in_db = Language.objects.create(code=language)
                languages.append(language_in_db)

            book_in_db.languages.clear()
            for language in languages:
                book_in_db.languages.add(language)

            ''' Make/update subjects. '''

            subjects = []
            for subject in book['subjects']:
                subject_in_db = Subject.objects.filter(name=subject)
                if subject_in_db.exists():
                    subject_in_db = subject_in_db[0]
                else:
                    subject_in_db = Subject.objects.create(name=subject)
                subjects.append(subject_in_db)

            book_in_db.subjects.clear()
            for subject in subjects:
                book_in_db.subjects.add(subject)

        except Exception as error:
            book_json = json.dumps(book, indent=4)
            log(
                '  Error while putting this book info in the database:\n',
                book_json,
                '\n'
            )
            raise error


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


class Command(BaseCommand):
    help = 'This replaces the catalog files with the latest ones.'

    def handle(self, *args, **options):
        try:
            date_and_time = strftime('%H:%M:%S on %B %d, %Y')
            log('Starting script at', date_and_time)

            log('  Making temporary directory...')
            if os.path.exists(TEMP_PATH):
                raise CommandError(
                    'The temporary path, `' + TEMP_PATH + '`, already exists.'
                )
            else:
                os.makedirs(TEMP_PATH)

            log('  Downloading compressed catalog...')
            urllib.request.urlretrieve(URL, DOWNLOAD_PATH)

            log('  Decompressing catalog...')
            if not os.path.exists(DOWNLOAD_PATH):
                os.makedirs(DOWNLOAD_PATH)
            with open(os.devnull, 'w') as null:
                call(
                    ['tar', 'fjvx', DOWNLOAD_PATH, '-C', TEMP_PATH],
                    stdout=null,
                    stderr=null
                )

            log('  Detecting stale directories...')
            if not os.path.exists(MOVE_TARGET_PATH):
                os.makedirs(MOVE_TARGET_PATH)
            new_directory_set = get_directory_set(MOVE_SOURCE_PATH)
            old_directory_set = get_directory_set(MOVE_TARGET_PATH)
            stale_directory_set = old_directory_set - new_directory_set

            log('  Removing stale directories and books...')
            for directory in stale_directory_set:
                book = Book.objects.filter(gutenberg_id=directory)
                book.delete()
                path = os.path.join(MOVE_TARGET_PATH, directory)
                shutil.rmtree(path)

            log('  Replacing old catalog...')
            with open(os.devnull, 'w') as null:
                with open(LOG_PATH, 'a') as log_file:
                    call(
                        [
                            'rsync',
                            '-va',
                            '--delete-after',
                            MOVE_SOURCE_PATH + '/',
                            MOVE_TARGET_PATH
                        ],
                        stdout=null,
                        stderr=log_file
                    )

            log('  Putting the catalog in the database...')
            put_catalog_in_db()

            log('  Removing temporary files...')
            shutil.rmtree(TEMP_PATH)

            log('Done!\n')
        except Exception as error:
            error_message = str(error)
            log('Error:', error_message)
            log('')
            shutil.rmtree(TEMP_PATH)

        send_log_email()
