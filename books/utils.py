import xml.etree.ElementTree as parser
import re


LINE_BREAK_PATTERN = re.compile(r'[ \t]*[\n\r]+[ \t]*')
NAMESPACES = {
    'dc': 'http://purl.org/dc/terms/',
    'dcam': 'http://purl.org/dc/dcam/',
    'pg': 'http://www.gutenberg.org/2009/pgterms/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
}


def fix_subtitles(title):
    """
    This formats subtitles with (semi)colons instead of new lines. The first
    subtitle is introduced with a colon, and the rest are introduced with
    semicolons.

    >>> fix_subtitles(u'First Across ...\r\nThe Story of ... \r\n'
    ... 'Being an investigation into ...')
    u'First Across ...: The Story of ...; Being an investigation into ...'
    """

    new_title = LINE_BREAK_PATTERN.sub(': ', title, 1)
    return LINE_BREAK_PATTERN.sub('; ', new_title)


def get_book(id, xml_file_path):
    """ Based on https://gist.github.com/andreasvc/b3b4189120d84dec8857 """

    # Parse the XML.
    document = None
    try:
        document = parser.parse(xml_file_path)
    except:
        raise Exception('The XML file could not be parsed.')

    # Get the book node.
    root = document.getroot()
    book = root.find('{%(pg)s}ebook' % NAMESPACES)

    result = {
        'id': int(id),
        'title': None,
        'authors': [],
        'type': None,
        'subjects': [],
        'languages': [],
        'formats': {},
        'downloads': None,
        'bookshelves': [],
        'copyright': None
    }

    # Authors
    creators = book.findall('.//{%(dc)s}creator' % NAMESPACES)
    for creator in creators:
        author = {'birth': None, 'death': None}
        name = creator.find('.//{%(pg)s}name' % NAMESPACES)
        if name is None:
            continue
        author['name'] = safe_unicode(name.text, encoding='UTF-8')
        birth = creator.find('.//{%(pg)s}birthdate' % NAMESPACES)
        if birth is not None:
            author['birth'] = int(birth.text)
        death = creator.find('.//{%(pg)s}deathdate' % NAMESPACES)
        if death is not None:
            author['death'] = int(death.text)
        result['authors'] += [author]

    # Title
    title = book.find('.//{%(dc)s}title' % NAMESPACES)
    if title is not None:
        result['title'] = fix_subtitles(
            safe_unicode(title.text, encoding='UTF-8')
        )

    # Subjects
    result['subjects'] = set()
    for subject in book.findall('.//{%(dc)s}subject' % NAMESPACES):
        subject_type = subject.find('.//{%(dcam)s}memberOf' % NAMESPACES)
        if subject_type is None:
            continue
        subject_type = subject_type.get('{%(rdf)s}resource' % NAMESPACES)
        value = subject.find('.//{%(rdf)s}value' % NAMESPACES)
        value = value.text
        if subject_type in ('%(dc)sLCSH' % NAMESPACES):
            result['subjects'].add(value)
    result['subjects'] = list(result['subjects'])
    result['subjects'].sort()

    # Book Shelves
    result['bookshelves'] = set()
    for bookshelf in book.findall('.//{%(pg)s}bookshelf' % NAMESPACES):
        value = bookshelf.find('.//{%(rdf)s}value' % NAMESPACES)
        if value is not None:
            result['bookshelves'].add(value.text)
    result['bookshelves'] = list(result['bookshelves'])

    # Copyright
    rights = book.find('.//{%(dc)s}rights' % NAMESPACES)
    if rights.text.startswith('Public domain in the USA.'):
        result['copyright'] = False
    elif rights.text.startswith('Copyrighted.'):
        result['copyright'] = True
    else:
        result['copyright'] = None

    # Formats (preferring image URLs to `noimages` URLs)
    for file in book.findall('.//{%(pg)s}file' % NAMESPACES):
        content_type = file.find('{%(dc)s}format//{%(rdf)s}value' % NAMESPACES)
        if (
            content_type.text not in result['formats']
            or 'noimages' in result['formats'][content_type.text]
        ):
            url = file.get('{%(rdf)s}about' % NAMESPACES)
            result['formats'][content_type.text] = url

    # Type
    book_type = book.find(
        './/{%(dc)s}type//{%(rdf)s}value' % NAMESPACES
    )
    if book_type is not None:
        result['type'] = book_type.text

    # Languages
    languages = book.findall(
        './/{%(dc)s}language//{%(rdf)s}value' % NAMESPACES
    )
    result['languages'] = [language.text for language in languages] or []

    # Download Count
    download_count = book.find('.//{%(pg)s}downloads' % NAMESPACES)
    if download_count is not None:
        result['downloads'] = int(download_count.text)

    return result


def safe_unicode(arg, *args, **kwargs):
    """ Coerce argument to Unicode if it's not already. """
    return arg if isinstance(arg, str) else str(arg, *args, **kwargs)
