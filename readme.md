Gutendex
========

Gutendex is a simple, self-hosted [web API](https://en.wikipedia.org/wiki/Web_API) for serving book
catalog information from [Project Gutenberg](https://www.gutenberg.org/wiki/Main_Page), an online
library of free ebooks.


Why?
----

Project Gutenberg can be a useful source of literature, but its large size makes it difficult to
access and analyse it on a large scale. Thus, an API of its catalog information is useful for
automating these tasks.


How does it work?
-----------------

Gutendex uses [Django](https://www.djangoproject.com) to download catalog data and serve it in a
simple [JSON](http://json.org) [REST](https://en.wikipedia.org/wiki/Representational_state_transfer)
API.

Project Gutenberg has no such public API of its own, but it publishes nightly archives of
complicated XML files. Gutendex downloads these files, stores their data in a database, and
publishes the data in a simpler format.


Installation
------------

See the [installation guide](https://github.com/garethbjohnson/gutendex/wiki/Installation-Guide).


API
---

When your server is up and running, you should see a home page that says "Gutendex" at the root URL
(e.g. `http://localhost:8000` by default when using `manage.py` to serve on your local machine).

You should run your own server, but you can test queries at [`gutendex.com`](http://gutendex.com).


### Lists of Books

Lists of book information in the database are queried using the API at `/books` (e.g.
[`gutendex.com/books`](http://gutendex.com/books)). Book data will be returned in the JSON format

```
{
  "count": <number>,
  "next": <string or null>,
  "previous": <string or null>,
  "results": <array of Books>
}
```

where `results` is an array of 0-32 book objects, `next` and `previous` are URLs to the next and
previous pages of results, and `count` in the total number of books for the query on all pages
combined.

Books are ordered by popularity, determined by their numbers of downloads from Project Gutenberg.

Parameters can also be added to book-list queries in a typical URL format. For example, to get the
first page of written by authors alive after 1899 and published in English or French, you can go to
[`/books?author_year_start=1900&languages=en,fr`](http://gutendex.com/books?author_year_start=1900&languages=en,fr)

You can find available query parameters below.

#### `author_year_start` and `author_year_end`
Use these to find books with at least one author alive in a given range of years. They must have
positive or negative integer values. For example,
[`/books?author_year_end=-499`](http://gutendex.com/books?author_year_end=-499) gives books with
authors alive before 500 BCE, and
[`/books?author_year_start=1800&author_year_end=1899`](http://gutendex.com/books?author_year_start=1800&author_year_end=1899)
gives books with authors alive in the 19th Century.

#### `ids`
Use this to list books with Project Gutenberg ID numbers in a given list of numbers. They must be
comma-separated positive integers. For example,
[`/books?ids=11,12,13`](http://gutendex.com/books?ids=11,12,13) gives books with ID numbers 12, 13,
and 14.

#### `languages`
Use this to find books in any of a list of languages. They must be comma-separated, two-character
language codes. For example, [`/books?languages=en`](http://gutendex.com/books?languages=en) gives
books in English, and [`/books?languages=fr,fi`](http://gutendex.com/books?languages=fr,fi) gives
books in either French or Finnish or both.

#### `mime_type`
Use this to find books with a given [MIME type](https://en.wikipedia.org/wiki/Media_type). Gutendex
gives every book with a MIME type *starting with* the value. For example,
[`/books?mime_type=text%2F`](http://gutendex.com/books?mime_type=text%2F) gives books with types
`text/html`, `text/plain; charset=us-ascii`, etc.; and
[`/books?mime_type=text%2Fhtml`](http://gutendex.com/books?mime_type=text%2Fhtml) gives books with
types `text/html`, `text/html; charset=utf-8`, etc.

#### `search`
Use this to search author names and book titles with given words. They must be separated by a space
(i.e. `%20` in URL-encoded format) and are case-insensitive. For example,
[`/books?search=dickens%20great`](http://gutendex.com/books?search=dickens%20great) includes *Great
Expectations* by Charles Dickens.

#### `topic`
Use this to search for a case-insensitive key-phrase in books' bookshelves or subjects. For example,
[`/books?topic=children`](http://gutendex.com/books?topic=children) gives books on the "Children's
Literature" bookshelf, with the subject "Sick children -- Fiction", and so on.


### Individual Books

Individual books can be found at `/book/<id>`, where `<id>` is the book's Project Gutenberg ID
number. Error responses will appear in this format:

```
{
  "detail": <string of error message>
}
```


### API Objects


Types of JSON objects served by Gutendex are given below.

#### Author

```
{
  "birth_year": <number or null>,
  "death_year": <number or null>,
  "name": <string>
}
```


#### Book

```
{
  "id": <number of Project Gutenberg ID>,
  "authors": <array of Authors>,
  "bookshelves": <array of strings>,
  "download_count": <number>,
  "formats": <Format>,
  "languages": <array of strings>,
  "media_type": <string>
  "subjects": <array of strings>,
  "title": <string>
}
```


#### Format

```
{
  <string of MIME-type>: <string of URL>,
  ...
}
```
