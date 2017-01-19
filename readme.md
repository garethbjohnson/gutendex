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

To use Gutendex, you must first have the following software installed:
* Python 3.5
* Postgres 9.5


### Make the Database

Make the Gutendex database using the following command as the necessary user for Postgres
(typically, this is `postgres`):

```
createdb gutendex
```

(You can replace `gutendex` above with whatever name you want, as long as you update the
`DATABASE_NAME` environment variable accordingly, as described below.)

Make a Postgres user for the database, and *remember the password that you enter*:

```
createuser -P gutendex
```

(You can also replace `gutendex` above with another user name, updating the `DATABASE_USER`
environment variable below.)

Now, open Postgres on the command line with

```
psql
```

and enter the following SQL:

```
GRANT ALL PRIVILEGES ON DATABASE gutendex TO gutendex;
```

(If you entered your own database and/or user name earlier, replace `gutendex` above with them,
respectively.)

Exit Postgres by pressing `ctrl+d` on your keyboard.


### Install Required Python Packages

Python packages required by Gutendex are listed with their version numbers in `requirements.txt`.

I recommend that you install these with [pip](https://pip.pypa.io/en/stable/) in a virtual
environment created with [Virtualenv](https://virtualenv.pypa.io/en/stable/). You can do this as the
root user in the Gutendex root directory like this:

```
pip install virtualenv
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

This creates a new directory, `venv`, which holds the files necessary files for the virtual
environment, and activates that environment. Later, when you are done working with Gutendex, you can
enter the `deactivate` command to exit the virtual environment.


### Create Environment Variables

A number of environment variables are used by Gutendex, and they are listed in
`gutendex/.env.template`.

I recommend that you copy this file to a new file called `.env` and edit the values after the `=`
sign on each line with the proper data. The Django project will automatically read this file when
the server starts.

Here are descriptions of each variable required:

#### `ADMIN_EMAILS`
This is a list of email addresses of the project administrators in `ADMIN_NAMES`. Addresses should
be separated by commas and be in the same quantity and order as the names in `ADMIN_NAMES`.

#### `ADMIN_NAMES`
This is a list of names of project administrators that will be emailed with catalog download logs
and various Django messages, such as security warnings. Names should be separated with commas.

#### `ALLOWED_HOSTS`
This is a list of domains and IP addresses on which you allow Gutendex to be served. Domains should
be separated by commas. To allow any subdomain of a domain, add a `.` before the domain (e.g.
`.gutendex.com` allows `gutendex.com`, `api.gutendex.com`, etc.). I recommend including `127.0.0.1`
and/or `localhost` for development and testing on your local machine.

#### `DATABASE_HOST`
This is the domain or IP address on which your Postgres database runs. It is typically `127.0.0.1`
for local databases.

#### `DATABASE_NAME`
This is the name of the Postgres database that you used. (Instructions for creating this database
are above.) I recommend `gutendex`.

#### `DATABASE_PASSWORD`
This is the password for `DATABASE_USER`.

#### `DATABASE_PORT`
This is the port number on which the Gutendex database runs. This will typically be `5432`.

#### `DATABASE_USER`
This is the name of a database user with all privileges for the Gutendex database. I recommend
`gutendex`.

#### `DEBUG`
This is a Django setting for displaying useful debugging information. `true` will show this
information in API responses when errors occur during development. **It is important for security
that you set this to `false` before serving Gutendex on a public address.**

#### `EMAIL_HOST`
This is the address of the [SMTP](https://en.wikipedia.org/wiki/Simple_Mail_Transfer_Protocol)
server that Gutendex will try to use when sending email. I recommend using
[Mailgun](https://www.mailgun.com).

#### `EMAIL_HOST_ADDRESS`
This is the email address where Gutendex email will appear to come from.

#### `EMAIL_HOST_PASSWORD`
This is the password for the the below `EMAIL_HOST_USER`.

#### `EMAIL_HOST_USER`
This is the user name that Gutendex will use to send email from the SMTP server in `EMAIL_HOST`.

#### `MANAGER_EMAILS`
This is a list of email addresses of the website managers in `MANAGER_NAMES`. Addresses should be
separated by commas and be in the same quantity and order as the names in `MANAGER_NAMES`.

#### `MANAGER_NAMES`
This is a list of names of website managers that can be emailed with various Django messages. Names
should be separated with commas.

#### `MEDIA_ROOT`
This is the path to a server directory where any API user media (currently nothing) can be stored.

#### `SECRET_KEY`
This is a password that Django uses for security reasons. It should be a long string of characters
that should be kept secret. You do not need to copy or remember it anywhere.

#### `STATIC_ROOT`
This is the path to a server directory where website assets, such as CSS styles for HTML pages, are
stored.


### Migrate the Database

Next, set up the database for storing the catalog data. Run this in the virtual environment
mentioned above:

```
./manage.py migrate
```


### Populate the Database

Enter the Project Gutenberg catalog data into the Gutendex database. This takes a long time (several
minutes on my machine):

```
./manage.py updatecatalog
```

This downloads a file archive of Project Gutenberg's catalog data and decompresses the files into a
new directory, `catalog_files`. It places the contained files in `catalog_files/rdf`, and it stores
a log in `catalog_files/log` and emails it to the administrators in the environment variables
mentioned above.

If your database already contains catalog data, the above command will update it with any new or
updated data from Project Gutenberg. I recommend that you schedule this command to run on your
server daily – for example, using `cron` on Unix-like machines – to keep your database up-to-date.


### Collect Static Files

To show styled HTML pages (i.e. the home page and error pages), you must put the necessary
stylesheets into a static-file directory:

```
./manage.py collectstatic
```


### Run the Server

Now you can serve your Django project. On your local machine, you can run do this with the following
command for development and testing purposes:

```
./manage.py runserver
```

#### Serving Publicly

In a production environment, I recommend using the [Apache v2 HTTP Server](http://httpd.apache.org)
instead. You can install this on Ubuntu 16 for use with Django with the following command:

```
apt install apache2 libapache2-mod-wsgi-py3
```

Next, you need to configure Apache to serve
* static files,
* [`robots.txt`](http://www.robotstxt.org/robotstxt.html),
* any future user media, and
* the web API itself.

You can do this by editing the file `/etc/apache2/sites-available/000-default.conf` on your server
and adding the following lines before the line containing `</VirtualHost>`, but replacing
`/path/to/gutendex` to the Gutendex path on your server:

```
	Alias /static /path/to/gutendex/static
	<Directory /path/to/gutendex/static>
		Require all granted
	</Directory>

	Alias /robots.txt /path/to/gutendex/static/robots.txt

	Alias /media /path/to/gutendex/media
	<Directory /path/to/gutendex/media>
		Require all granted
	</Directory>

	<Directory /path/to/gutendex/gutendex>
		<Files wsgi.py>
			Require all granted
		</Files>
	</Directory>

	WSGIDaemonProcess gutendex python-home=/path/to/gutendex/venv python-path=/path/to/gutendex
	WSGIProcessGroup gutendex
	WSGIScriptAlias / /path/to/gutendex/gutendex/wsgi.py
```

You also need to give Apache's web server user permission to access the Gutendex files. You can do
this with the following command, again replacing `/path/to/gutendex` to the Gutendex path on your
server:

```
chown :www-data /path/to/gutendex
```

You can now serve Gutendex with this command:

```
service apache2 restart
```

You should also collect the static files and run the above command again whenever you add or update
Gutendex files.


API
---

When your server is up and running, you should see a home page that says "Gutendex" at the root URL
(e.g. `http://localhost:8000` by default when using `manage.py` to serve on your local machine).


### Lists of Books

Lists of book information in the database are queried using the API at `/books` (e.g.
`http://localhost:8000/books`). Book data will be returned in the JSON format

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
first page of written by authors alive after 1899 and published in English or French, you can go
here:

```
/books?author_year_start=1900&languages=en,fr
```

You can find available query parameters below.

#### `author_year_start` and `author_year_end`
Use these to find books with at least one author alive in a given range of years. They must have
positive or negative integer values. For example, `/books?author_year_end=-499` gives books with
authors alive before 500 BCE, and `/books?author_year_start=1800&author_year_end=1899` gives books
with authors alive in the 19th Century.

#### `ids`
Use this to list books with Project Gutenberg ID numbers in a given list of numbers. They must be
comma-separated positive integers. For example, `/books?ids=11,12,13` gives books with ID numbers
12, 13, and 14.

#### `languages`
Use this to find books in any of a list of languages. They must be comma-separated, two-character
language codes. For example, `/books?languages=en` gives books in English, and
`/books?languages=fr,fi` gives books in either French or Finnish or both.

#### `mime_type`
Use this to find books with a given [MIME type](https://en.wikipedia.org/wiki/Media_type). Gutendex
gives every book with a MIME type *starting with* the value. For example, `/books?mime_type=text%2F`
gives books with types `text/html`, `text/plain; charset=us-ascii`, etc.; and
`/books?mime_type=text%2Fhtml` gives books with types `text/html`, `text/html; charset=utf-8`, etc.

#### `search`
Use this to search author names and book titles with given words. They must be separated by a space
(i.e. `%20` in URL-encoded format) and are case-insensitive. For example,
`/books?search=dickens%20great` includes *Great Expectations* by Charles Dickens.

#### `topic`
Use this to search for a case-insensitive key-phrase in books' bookshelves or subjects. For example,
`/books?topic=children` gives books on the "Children's Literature" bookshelf, with the subject "Sick
children -- Fiction", and so on.


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
