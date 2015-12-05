"""
Defines application-specific settings. This file should not be modified:
user-defined overrides can be added to the site-wide settings file.

The following settings are defined herein:

BDR_ARCHIVE_READERS
    A list of qualified class names, each of which extending the `Archive`
    class defined in the `bdr.utils.archives` module.

BDR_UNCOMPRESS_BIN
    The path to the ``uncompress`` binary (typically ``/bin/uncompress``) or
    another executable that is capable of decompressing the ``compress`` format
    (for example, ``/bin/gunzip``).

    The binary must support receiving data through standard input (``stdin``)
    and the ``-c`` flag for output to standard output (``stdout``).

    This setting is required if the
    :py:class:`bdr.utils.archives.CompressArchive` class is included as an
    archive reader.

    The reader itself should be added with:

        ``BDR_ARCHIVE_READERS = ['bdr.utils.archives.CompressArchive']``

BDR_REMOTE_TRANSPORTS
    A dictionary that maps URL scheme names to qualified class names. These
    classes must extend the `Transport` class defined in the
    `bdr.utils.transports` module.
"""

from django.conf import settings

__all__ = []
__author__ = "Michael Winter (mail@michael-winter.me.uk)"
__license__ = """
    Biological Dataset Repository: data archival and retrieval.
    Copyright (C) 2015  Michael Winter

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
    """

ARCHIVE_READERS = getattr(settings, 'BDR_ARCHIVE_READERS', [])
ARCHIVE_READERS.extend(['bdr.utils.archives.TarArchive', 'bdr.utils.archives.ZipArchive',
                        'bdr.utils.archives.GzipArchive', 'bdr.utils.archives.MockArchive'])

UNCOMPRESS_BIN = getattr(settings, 'BDR_UNCOMPRESS_BIN', None)

REMOTE_TRANSPORTS = getattr(settings, 'BDR_REMOTE_TRANSPORTS', {})
REMOTE_TRANSPORTS.update({'ftp': 'bdr.utils.transports.FtpTransport',
                          'http': 'bdr.utils.transports.HttpTransport'})
