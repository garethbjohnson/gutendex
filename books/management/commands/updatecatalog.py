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

def get_id(file):
    id = file.name.split('/')[2]
    try:
        id = int(id)
    except ValueError:
        id = None
    return id

def put_catalog_in_db(tar):
    c = 0
    for file in tar:
        if c <= 0:
            c += 1
            f = tar.extractfile(file)
            id = get_id(file)
            #creates a string of the xml
            content = f.read().decode('utf-8')
            print(f"ID == {get_id(file)}")
            print(content)
            if (id > 0) and (id % 500 == 0):
                log('    %d' % id)

            book = utils.get_book(id, content)
            print(book)
            # try:
            ''' Make/update the book. '''

            book_in_db = Book.objects.filter(gutenberg_id=id)

            if book_in_db.exists():
                book_in_db = book_in_db[0]
                book_in_db.copyright = book['copyright']
                book_in_db.download_count = book['downloads']
                book_in_db.media_type = book['type']
                book_in_db.title = book['title']
                book_in_db.save()
            else:
                book_in_db = Book.objects.create(
                    gutenberg_id=id,
                    copyright=book['copyright'],
                    download_count=book['downloads'],
                    media_type=book['type'],
                    title=book['title']
                )

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
                book_in_db.format.add(format_in_db)
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

            # except Exception as error:
            #     book_json = json.dumps(book, indent=4)
            #     log(
            #         '  Error while putting this book info in the database:\n',
            #         book_json,
            #         '\n'
            #     )
            #     raise error


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
#todo
# def detect_stale_entries():
#     log('  Detecting stale directories...')
#     if not os.path.exists(MOVE_TARGET_PATH):
#         os.makedirs(MOVE_TARGET_PATH)
#     new_directory_set = get_directory_set(MOVE_SOURCE_PATH)
#     old_directory_set = get_directory_set(MOVE_TARGET_PATH)
#     stale_directory_set = old_directory_set - new_directory_set

#     log('  Removing stale directories and books...')
#     for directory in stale_directory_set:
#         try:
#             book_id = int(directory)
#         except ValueError:
#             # Ignore the directory if its name isn't a book ID number.
#             continue
#         book = Book.objects.filter(gutenberg_id=book_id)
#         book.delete()
#         path = os.path.join(MOVE_TARGET_PATH, directory)
#         shutil.rmtree(path)
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
        put_catalog_in_db(tar)
    
        log('  Removing temporary files...')
        shutil.rmtree(TEMP_PATH)

        log('Done!\n')
        # except Exception as error:
        #     error_message = str(error)
        #     log('Error:', error_message)
        #     log('')
        #     shutil.rmtree(TEMP_PATH)

        # # send_log_email()
