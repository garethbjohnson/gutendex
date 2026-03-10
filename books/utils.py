import defusedxml.ElementTree as parser
import re


LINE_BREAK_PATTERN = re.compile(r'[ \t]*[\n\r]+[ \t]*')
NAMESPACES = {
    'dc': 'http://purl.org/dc/terms/',
    'dcam': 'http://purl.org/dc/dcam/',
    'marcrel': 'http://id.loc.gov/vocabulary/relators/',
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
        'summaries': [],
        'editors': [],
        'translators': [],
        'type': None,
        'subjects': [],
        'languages': [],
        'formats': {},
        'downloads': None,
        'bookshelves': [],
        'copyright': None,
        'published_year': None,
        'wikipedia_url': '',
        'reading_score': '',
        'reading_score_value': None,
    }

    # Authors
    creators = book.findall('.//{%(dc)s}creator' % NAMESPACES)
    for creator in creators:
        author = get_person(creator)
        if author is not None:
            result['authors'] += [author]

    # Editors
    editor_elements = book.findall('.//{%(marcrel)s}edt' % NAMESPACES)
    for editor_element in editor_elements:
        editor = get_person(editor_element)
        if editor is not None:
            result['editors'] += [editor]

    # Translators
    translator_elements = book.findall('.//{%(marcrel)s}trl' % NAMESPACES)
    for translator_element in translator_elements:
        translator = get_person(translator_element)
        if translator is not None:
            result['translators'] += [translator]

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
    result['type'] = 'Text' if book_type is None else book_type.text

    # Languages
    languages = book.findall(
        './/{%(dc)s}language//{%(rdf)s}value' % NAMESPACES
    )
    result['languages'] = [language.text for language in languages] or []

    # Download Count
    download_count = book.find('.//{%(pg)s}downloads' % NAMESPACES)
    if download_count is not None:
        result['downloads'] = int(download_count.text)
    
    # Summary
    summaries = book.findall('.//{%(pg)s}marc520' % NAMESPACES)
    result['summaries'] = [summary.text for summary in summaries]

    # Published year (dcterms:issued → YYYY-MM-DD → int year)
    issued = book.find('.//{%(dc)s}issued' % NAMESPACES)
    if issued is not None and issued.text:
        try:
            result['published_year'] = int(issued.text[:4])
        except (ValueError, TypeError):
            pass

    # Wikipedia URL (from dcterms:description)
    for desc in book.findall('.//{%(dc)s}description' % NAMESPACES):
        if desc.text:
            m = re.search(r'https?://[^\s]*wikipedia\.org[^\s]*', desc.text)
            if m:
                result['wikipedia_url'] = m.group(0)
                break

    # Reading ease (pgterms:marc908) — e.g. "Reading ease score: 78.7 (7th grade). Fairly easy to read."
    marc908_el = book.find('.//{%(pg)s}marc908' % NAMESPACES)
    if marc908_el is not None and marc908_el.text:
        result['reading_score'] = marc908_el.text
        m = re.search(r'Reading ease score:\s*([\d.]+)', marc908_el.text)
        if m:
            try:
                result['reading_score_value'] = float(m.group(1))
            except ValueError:
                pass

    return result


def get_person(person_element):
    name = person_element.find('.//{%(pg)s}name' % NAMESPACES)

    if name is None:
        return None

    # Extract Gutenberg agent ID from rdf:about on the pg:agent child element
    gutenberg_id = None
    agent_el = person_element.find('{%(pg)s}agent' % NAMESPACES)
    if agent_el is not None:
        about = agent_el.get('{%(rdf)s}about' % NAMESPACES, '')
        m = re.search(r'(\d+)$', about)  # "2009/agents/37" → 37
        if m:
            gutenberg_id = int(m.group(1))

    person = {
        'gutenberg_id': gutenberg_id,
        'birth': None,
        'death': None,
        'name': safe_unicode(name.text, encoding='UTF-8'),
    }

    birth = person_element.find('.//{%(pg)s}birthdate' % NAMESPACES)

    if birth is not None:
        person['birth'] = int(birth.text)

    death = person_element.find('.//{%(pg)s}deathdate' % NAMESPACES)

    if death is not None:
        person['death'] = int(death.text)

    return person


def safe_unicode(arg, *args, **kwargs):
    """ Coerce argument to Unicode if it's not already. """
    return arg if isinstance(arg, str) else str(arg, *args, **kwargs)
