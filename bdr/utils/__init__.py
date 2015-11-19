"""
This package contains various utilities used by the repository.
"""

from datetime import datetime, timedelta, tzinfo

from django.core.files import File

__all__ = ["utc", "File"]
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


class RemoteFile(File):
    """
    A file-like object that extends `File` to add tracking modification time.
    """

    # noinspection PyShadowingBuiltins
    def __init__(self, file, name=None, size=-1, modified_time=None):
        super(RemoteFile, self).__init__(file, name)
        self._modified_time = modified_time
        if size != -1:
            self.size = size

    def _get_modified_time(self):
        if self._modified_time is None:
            pass
        return self._modified_time


class UTC(tzinfo):
    """Represents the Co-ordinated Universal Time zone."""
    __OFFSET = timedelta(0)

    def utcoffset(self, date_time):
        """Return the offset (in minutes) from UTC."""
        return self.__OFFSET

    def dst(self, date_time):
        """Return the offset (in minutes) from UTC when daylight-savings time is in effect."""
        return self.__OFFSET

    def tzname(self, date_time):
        """Return the name of this timezone."""
        return 'UTC'
utc = UTC()


def to_epoch(dt):
    """Convert a datetime to the number of second from epoch (1 January 1970)."""
    return (dt - _epoch).total_seconds()

_epoch = datetime(1970, 1, 1, tzinfo=utc)


def repr_builder(obj, field_names):
    module = type(obj).__module__
    class_name = type(obj).__name__
    parameters = ', '.join(["{0}={1!r}".format(field, getattr(obj, field))
                            for field in field_names])
    return "{0}.{1}({2})".format(module, class_name, parameters)
