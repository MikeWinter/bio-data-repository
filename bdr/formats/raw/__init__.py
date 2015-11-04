"""
Files of the raw format type cannot be processed by the repository and are
exported as-is to the user.
"""

from .. import Reader as BaseReader, Record as BaseRecord, Writer as BaseWriter
from .views import RawFormatDetailView

__all__ = ["Record", "Reader", "Writer"]
__author__ = "Michael Winter (mail@michael-winter.me.uk)"
__license__ = """
    Copyright (C) 2015 Michael Winter

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
    """

name = "raw"
views = {
    "view": RawFormatDetailView.as_view(),
}


class Reader(BaseReader):
    """Reads files in chunks."""

    chunk_size = 8 * 1024 * 1024

    def __iter__(self):
        while True:
            chunk = self._stream.read(self.chunk_size)
            if not chunk:
                break
            yield Record(chunk)


# Base class implements all abstract methods
# noinspection PyAbstractClass
class Record(BaseRecord):
    """Represents a chunk of file data."""

    def __init__(self, data):
        super(Record, self).__init__()
        self._fields = ['data']
        self._data['data'] = data

    def __str__(self):
        return self.get('data')


class Writer(BaseWriter):
    """A no-op converter that returns chunks as-is."""

    pass
