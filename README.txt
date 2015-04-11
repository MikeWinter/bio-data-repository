Biological Dataset Repository
=============================

Requirements
------------
The application submitted herein requires Python 2.7 and Django 1.6. It has been tested successfully on the Teaching
departmental server and a guide to this end has been included later in this file. However, it should be noted that a
running version is available at: http://paccanarolab.org/explorer/


Running the application
-----------------------
Below are a series of steps that should be followed if the application is to be run locally.

1) Edit the STATIC_ROOT path in explorer/settings.py. This can be found near the end of that file and must be an
   absolute path that points to the bdr/frontend/static/ subdirectory.
2) Generate the database by running:    ./manage.py syncdb
3) (Optional) Run the test suite with:  ./manage.py test
4) Start the server by running:         ./manage.py runserver
5) Navigate to the host name and port as shown by the output of (4) after appending /explorer/ to the URL. This would
   typically be: http://127.0.0.1:8000/explorer/


Legal
-----
This software is Copyright (c) 2015 Michael Winter and released under the GNU Public License v2+ (see LICENSE).

* Bootstrap is Copyright (c) 2011-2015 Twitter, Inc and licensed under the MIT License (see LICENSE-bootstrap).
* The Flatly Bootswatch theme is Copyright (c) 2014 Thomas Park and licensed under the MIT License (see
  LICENSE-bootswatch).
* Django Restless is Copyright (c) 2012-14 Django Restless contributors and licensed under the MIT License (see
  LICENSE-restless).
* httplib2 is Copyright (c) 2006 Joe Gregorio and licensed under the MIT License (see LICENSE-httplib2).
* jQuery is Copyright (c) 2015 The jQuery Foundation and licensed under the MIT License (see LICENSE-jquery).
* The Lato font is Copyright (c) 2010-14 Lukasz Dziedzic and licensed under the SIL Open Font License 1.1 (see
  LICENSE-lato).
* The logo for this website is a derivative work of an image released into the public domain by pixabay
  (http://pixabay.com).
* The Royal Holloway, University of London logo is a trademark of Royal Holloway, University of London.
* typeahead.js is Copyright (c) 2013-2014 Twitter, Inc and licensed under the MIT License (see LICENSE-typeaheadjs).
* xdelta3 is Copyright (c) 2001-07 Joshua Macdonald and licensed under the GNU Public License v2+ (see
  xdelta3-py/COPYING). The modified source code is available in the xdelta3-py subdirectory; the original 3.0.8 release
  is included as a Zip archive (xdelta3-3.0.8.zip) also available from <http://xdelta.org/>.
