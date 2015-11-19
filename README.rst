=============================
Biological Dataset Repository
=============================

Requirements
------------
This application was written for Python 2.7 and Django 1.6. Later versions may also work but, given substantive changes
present in these editions and lack of testing, this cannot be guaranteed.

In addition to Django, the following libraries are also required:

* djangodelta
* django-bootstrap3_
* httplib2_
* locket_

With the exception of djangodelta, these can be obtained separately from PyPI using pip or added during the setup
process (see below). Please contact the author for the source distribution of djangodelta.

.. _django-bootstrap3: https://pypi.python.org/pypi/django-bootstrap3/6.2.2
.. _httplib2: https://pypi.python.org/pypi/httplib2/0.9.2
.. _locket: https://pypi.python.org/pypi/locket


Installation
------------
It is expected that a Django project environment will already be setup. As this is an application, it cannot be run
directly by a Web server. However, it only needs appropriate settings and inclusion in the URL routing list to become
available.

1. Run the ``setup.py`` script. This will install both the prerequisites and this application.
2. Edit the ``settings.py`` file in your project space:

    a. Add the following applications to the ``INSTALLED_APPS`` tuple:
    
        * ``django.contrib.contenttypes``
        * ``django.contrib.formtools``
        * ``django.contrib.humanize``
        * ``django.contrib.messages``
        * ``django.contrib.sessions``
        * ``django.contrib.staticfiles``
        * ``bootstrap3``
        * ``bdr``

    b. Ensure that at least the following middleware classes are included in the ``MIDDLEWARE_CLASSES`` tuple:
    
        * ``django.middleware.common.CommonMiddleware``
        * ``django.contrib.sessions.middleware.SessionMiddleware``
        * ``django.middleware.gzip.GZipMiddleware``
        * ``django.middleware.csrf.CsrfViewMiddleware``
        * ``django.contrib.auth.middleware.AuthenticationMiddleware``
        * ``django.contrib.messages.middleware.MessageMiddleware``
        * ``django.middleware.http.ConditionalGetMiddleware``

    c. Set ``MEDIA_ROOT`` to a writable path. The data files written by the repository will be placed in subdirectories
       at this location.
    d. Ensure a suitable default database backend is configured in the ``DATABASES`` map. Sqlite3 will function
       adequately for light use but alternatives such as MySQL and PostgreSQL will be more scalable.
    e. Configure the ``STATIC_URL`` and ``STATIC_ROOT`` settings. Application assets will be copied to the latter path.
    f. Define the ``BOOTSTRAP3`` configuration dictionary. It is recommended that this be set to::

        BOOTSTRAP3 = {
            "css_url": "//maxcdn.bootstrapcdn.com/bootswatch/3.3.5/flatly/bootstrap.min.css",
            "theme_url": "".join((STATIC_URL, "bdr/css/theme.css")),
            "include_jquery": True,
            "field_renderers": {
                "default": "bdr.utils.bootstrap.FieldRenderer",
                "inline": "bdr.utils.bootstrap.InlineFieldRenderer",
            },
            "set_placeholder": False,
        }

       Forms may render unexpectedly with different settings so caution is advised.
3. Import the application URL routing list by editing ``urls.py`` to include::

    url(r'^', include('bdr.urls', namespace='bdr', app_name='bdr')),

   The path prefix (empty in the example above) can be modified if you wish to deploy the application somewhere other
   than the root URL.
4. Initialise the database using the manage script: ``./manage.py syncdb``
5. Extract the application assets: ``./manage.py collectstatic``


Legal
-----
This software is Copyright (c) 2015 Michael Winter and released under the GNU Public License v2 (see LICENSE).

* Bootstrap is Copyright (c) 2011-2015 Twitter, Inc and licensed under the MIT License (see LICENSE-bootstrap).
* The Flatly Bootswatch theme is Copyright (c) 2014 Thomas Park and licensed under the MIT License (see
  LICENSE-bootswatch).
* Django is a trademark of the Django Software Foundation and licensed under the BSD license.
* httplib2 is Copyright (c) 2006 Joe Gregorio and licensed under the MIT License (see LICENSE-httplib2).
* jQuery is Copyright (c) 2015 The jQuery Foundation and licensed under the MIT License (see LICENSE-jquery).
* The Lato font is Copyright (c) 2010-14 Lukasz Dziedzic and licensed under the SIL Open Font License 1.1 (see
  LICENSE-lato).
* The logo for this website is a derivative work of an image released into the public domain by pixabay
  (http://pixabay.com).
* Python is a trademark of the Python Software Foundation and licensed under the Python License.
* The Royal Holloway, University of London logo is a trademark of Royal Holloway, University of London.
* typeahead.js is Copyright (c) 2013-2014 Twitter, Inc and licensed under the MIT License (see LICENSE-typeaheadjs).
* The typeahead.js compatibility stylesheet for Bootstrap 3 is Copyright (c) 2014 Shawn Zhou and licensed under the
  MIT License (see LICENSE-typeaheadjs).
* xdelta3 is Copyright (c) 2001-07 Joshua Macdonald and licensed under the GNU Public License v2.
