"""
Files of the simple format type contain tabular data with simple rows and
columns.
"""

import csv
try:
    # noinspection PyPep8Naming
    import cPickle as pickle
except ImportError:
    import pickle

from ...views.formats import FormatDeleteView
from .. import Reader as BaseReader, Record as BaseRecord, Writer as BaseWriter
from .views import SimpleFormatDetailView, SimpleFormatCreateView, SimpleFormatEditView

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

name = "simple"
views = {
    "view": SimpleFormatDetailView.as_view(),
    "create": SimpleFormatCreateView.as_view(),
    "edit": SimpleFormatEditView.as_view(),
    "delete": FormatDeleteView.as_view(),
}


# Base class implements all abstract methods
# noinspection PyAbstractClass
class Record(BaseRecord):
    """
    Represents a record within a simple, columnar data file composed of one or
    more fields.
    """

    def __init__(self, names, data):
        self._fields = names
        self._data = dict(zip(names, data))


class Reader(BaseReader):
    """
    Parses line-based, columnar files into discrete records.

    Instances of this type are iterable, returning records in file order.
    """
    # Metadata contains:
    #   * comment:   The character used to denote comments.
    #   * delimiter: The separating character used between fields.
    #   * quotechar: The character used to quote values containing other
    #                special characters.

    def __init__(self, stream, metadata=""):
        options = pickle.loads(metadata)
        super(Reader, self).__init__(stream, options)
        if "quotechar" not in options:
            options.update(quoting=csv.QUOTE_NONE)
        self._parser = csv.reader(stream, **options)

    def __iter__(self):
        """
        :raises IOError: if the number of parsed columns does not match that
        specified by the format definition.
        """
        comment_char = self._metadata.get("comment")
        field_names = self._metadata["fields"]
        field_count = len(field_names)
        for data in self._parser:
            if comment_char and data[0].startswith(comment_char):
                continue
            if len(data) != field_count:
                raise IOError("Unrecognised format")
            yield Record(field_names, data)


class Writer(BaseWriter):
    """
    Converts records to nominally identical types, but with the option to elide
    fields.
    """

    def __init__(self, stream, metadata="", fields=None):
        options = pickle.loads(metadata)
        if fields is None:
            fields = options["fields"].keys()
        super(Writer, self).__init__(stream, options, fields)
        self._impl = csv.writer(stream, **options)

    def write(self, record):
        """
        Write the given record to the output stream wrapped by this writer.

        :param record: The record to write.
        :type record: Record
        """
        values = [record[field] for field in self._fields]
        self._impl.writerow(values)
