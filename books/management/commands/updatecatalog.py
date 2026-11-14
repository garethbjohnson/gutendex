from subprocess import call
import os
import shutil
import requests
from time import strftime, sleep

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from books import utils
from books.models import *


TEMP_PATH = settings.CATALOG_TEMP_DIR

URL = 'https://gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2'
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


def download_file(url, path, retries=5):
    for i in range(retries):
        try:
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            return
        except (requests.exceptions.RequestException, Exception) as e:
            if i == retries - 1:
                raise
            log(f'  Download failed ({e}). Retrying in 5 seconds... ({i + 1}/{retries})')
            sleep(5)


def bulk_create_in_batches(manager, objects, batch_size=500):
    for start in range(0, len(objects), batch_size):
        manager.bulk_create(
            objects[start:start + batch_size],
            batch_size=batch_size
        )


def delete_in_batches(manager, book_ids, batch_size=5000):
    for start in range(0, len(book_ids), batch_size):
        manager.filter(
            book_id__in=book_ids[start:start + batch_size]
        ).delete()


def get_or_create_many(model, field_name, values, objects):
    new_objects = [
        model(**{field_name: value})
        for value in set(values)
        if value not in objects
    ]
    bulk_create_in_batches(model.objects, new_objects)
    objects.update({
        getattr(obj, field_name): obj for obj in new_objects
    })


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
    existing_books = {
        book.gutenberg_id: book for book in Book.objects.all()
    }
    people = {}
    for person in Person.objects.all():
        people.setdefault(
            (person.name, person.birth_year, person.death_year),
            person
        )
    bookshelves = {obj.name: obj for obj in Bookshelf.objects.all()}
    languages = {obj.code: obj for obj in Language.objects.all()}
    subjects = {obj.name: obj for obj in Subject.objects.all()}

    relation_specs = [
        (Book.authors.through, 'person', 'authors'),
        (Book.editors.through, 'person', 'editors'),
        (Book.translators.through, 'person', 'translators'),
        (Book.bookshelves.through, 'bookshelf', 'bookshelves'),
        (Book.languages.through, 'language', 'languages'),
        (Book.subjects.through, 'subject', 'subjects'),
    ]
    relation_objects = {
        'authors': people,
        'editors': people,
        'translators': people,
        'bookshelves': bookshelves,
        'languages': languages,
        'subjects': subjects,
    }

    batch_size = 500
    for start in range(0, len(book_ids), batch_size):
        batch_ids = book_ids[start:start + batch_size]
        books = {}
        for book_id in batch_ids:
            directory = str(book_id)
            book_path = os.path.join(
                settings.CATALOG_RDF_DIR,
                directory,
                'pg' + directory + '.rdf'
            )
            books[book_id] = utils.get_book(book_id, book_path)

        with transaction.atomic():
            new_books = []
            updated_books = []
            book_objects = {}
            for book_id, data in books.items():
                book = existing_books.get(book_id)
                if book is None:
                    book = Book(gutenberg_id=book_id)
                    new_books.append(book)
                else:
                    updated_books.append(book)

                book.copyright = data['copyright']
                book.download_count = data['downloads']
                book.media_type = data['type']
                book.title = data['title']
                book_objects[book_id] = book

            bulk_create_in_batches(Book.objects, new_books)
            existing_books.update({
                book.gutenberg_id: book for book in new_books
            })
            for batch_start in range(0, len(updated_books), batch_size):
                Book.objects.bulk_update(
                    updated_books[batch_start:batch_start + batch_size],
                    ['copyright', 'download_count', 'media_type', 'title'],
                    batch_size=batch_size
                )

            people_data = {}
            for data in books.values():
                for person_data in (
                    data['authors'] + data['editors'] + data['translators']
                ):
                    key = (
                        person_data['name'],
                        person_data['birth'],
                        person_data['death']
                    )
                    people_data.setdefault(key, person_data)
            new_people = [
                Person(
                    name=key[0],
                    birth_year=key[1],
                    death_year=key[2]
                )
                for key in people_data
                if key not in people
            ]
            bulk_create_in_batches(Person.objects, new_people)
            people.update({
                (person.name, person.birth_year, person.death_year): person
                for person in new_people
            })

            get_or_create_many(
                Bookshelf,
                'name',
                [value for data in books.values() for value in data['bookshelves']],
                bookshelves
            )
            get_or_create_many(
                Language,
                'code',
                [value for data in books.values() for value in data['languages']],
                languages
            )
            get_or_create_many(
                Subject,
                'name',
                [value for data in books.values() for value in data['subjects']],
                subjects
            )

            database_book_ids = [
                book.id for book in book_objects.values()
            ]
            for through, _, _ in relation_specs:
                delete_in_batches(through.objects, database_book_ids)
            delete_in_batches(Format.objects, database_book_ids)
            delete_in_batches(Summary.objects, database_book_ids)

            for through, related_field, data_field in relation_specs:
                seen = set()
                rows = []
                for book_id, data in books.items():
                    if related_field == 'person':
                        related_ids = [
                            relation_objects[data_field][
                                (person['name'], person['birth'], person['death'])
                            ].id
                            for person in data[data_field]
                        ]
                    else:
                        related_ids = [
                            relation_objects[data_field][value].id
                            for value in data[data_field]
                        ]
                    for related_id in related_ids:
                        key = (book_id, related_id)
                        if key not in seen:
                            seen.add(key)
                            rows.append(through(
                                book_id=book_objects[book_id].id,
                                **{related_field + '_id': related_id}
                            ))
                bulk_create_in_batches(through.objects, rows)

            formats = []
            summaries = []
            for book_id, data in books.items():
                formats.extend(
                    Format(
                        book=book_objects[book_id],
                        mime_type=mime_type,
                        url=url
                    )
                    for mime_type, url in data['formats'].items()
                )
                summaries.extend(
                    Summary(book=book_objects[book_id], text=text)
                    for text in set(data['summaries'])
                )
            bulk_create_in_batches(Format.objects, formats)
            bulk_create_in_batches(Summary.objects, summaries)

        log('    Imported %d of %d books' % (
            min(start + batch_size, len(book_ids)),
            len(book_ids)
        ))

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
            download_file(URL, DOWNLOAD_PATH)

            log('  Decompressing catalog...')

            with open(os.devnull, 'w') as null:
                result = call(
                    ['tar', 'fjvx', DOWNLOAD_PATH, '-C', TEMP_PATH],
                    stdout=null,
                    stderr=null)
            if result:
                raise CommandError('Could not decompress the downloaded catalog.')

            log('  Detecting stale directories...')
            if not os.path.exists(MOVE_TARGET_PATH):
                os.makedirs(MOVE_TARGET_PATH)
            new_directory_set = get_directory_set(MOVE_SOURCE_PATH)
            old_directory_set = get_directory_set(MOVE_TARGET_PATH)
            stale_directory_set = old_directory_set - new_directory_set

            log('  Removing stale directories and books...')
            for directory in stale_directory_set:
                try:
                    book_id = int(directory)
                except ValueError:
                    # Ignore the directory if its name isn't a book ID number.
                    continue
                book = Book.objects.filter(gutenberg_id=book_id)
                book.delete()
                path = os.path.join(MOVE_TARGET_PATH, directory)
                shutil.rmtree(path)

            log('  Replacing old catalog files...')
            shutil.copytree(
                MOVE_SOURCE_PATH,
                MOVE_TARGET_PATH,
                dirs_exist_ok=True
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
            if os.path.exists(TEMP_PATH):
                shutil.rmtree(TEMP_PATH)
            raise CommandError(error_message) from error

        send_log_email()
