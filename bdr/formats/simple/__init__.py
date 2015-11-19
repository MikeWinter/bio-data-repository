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

from .. import Reader as BaseReader, Record as BaseRecord, Converter as BaseConverter
from .views import (SimpleFormatDetailView, SimpleFormatCreateView, SimpleFormatEditView, SimpleFormatDeleteView,
                    SimpleRevisionExportView)

__all__ = ["Record", "Reader", "Writer"]
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

name = "simple"
views = {
    "view": SimpleFormatDetailView.as_view(),
    "create": SimpleFormatCreateView.as_view(),
    "edit": SimpleFormatEditView.as_view(),
    "delete": SimpleFormatDeleteView.as_view(),
    "export": SimpleRevisionExportView.as_view(),
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

    def __init__(self, stream, escape, quote, separator, **kwargs):
        super(Reader, self).__init__(stream, **kwargs)
        options = {}
        if quote:
            options["quotechar"] = str(quote)
        else:
            options["quoting"] = csv.QUOTE_NONE
        if escape:
            options["escapechar"] = str(escape)
            options["doublequote"] = False
        if separator:
            options["delimiter"] = str(separator)
        self._parser = csv.reader(stream, **options)

    def __iter__(self):
        """
        :raises IOError: if the number of parsed columns does not match that
        specified by the format definition.
        """
        comment_char = self._options["comment"]
        field_names = self._options["fields"]
        field_count = len(field_names)
        for data in self._parser:
            if comment_char and data[0].startswith(comment_char):
                continue
            if len(data) != field_count:
                raise IOError("Unrecognised format")
            yield Record(field_names, data)


class Converter(BaseConverter):
    """
    Converts records to nominally identical types, but with the option to elide
    fields.
    """

    def __init__(self, reader, fields, comment, escape, line_terminator, quote, separator, **kwargs):
        super(Converter, self).__init__(reader, kwargs, fields)
        self.comment_char = comment
        self.escape_char = escape
        self.quote_char = quote
        self.separator_char = separator
        self.line_terminator = line_terminator

    def __iter__(self):
        for record in self._reader:
            values = []
            for field in self._fields:
                value = self.prepare_value(record[field])
                values.append(value)
            yield self.separator_char.join(values) + self.line_terminator

    def prepare_value(self, value):
        """
        Make a value safe for output according the options specified for
        conversion.

        If a value contains special characters, these must be escaped or quoted
        as determined by the conversion settings. This includes literal escape
        and quote characters (if applicable).

        :param value: The value to make safe.
        :type value: str | unicode
        :return: The equivalent escaped or quoted value.
        :rtype: str | unicode
        :raise ValueError: if the conversion rules will result in emitting a
                           value containing ambiguous special characters.
        """
        if self.escape_char:
            value = value.replace(self.escape_char, self.escape_char * 2)
        if self.quote_char:
            replacement = self.escape_char + self.quote_char if self.escape_char else self.quote_char * 2
            value = value.replace(self.quote_char, replacement)
            if value.startswith(self.comment_char) or self.separator_char in value or self.line_terminator in value:
                value = "{0}{1}{0}".format(self.quote_char, value)
        elif self.escape_char:
            if value.startswith(self.comment_char):
                value = self.escape_char + value
            value = value.replace(self.separator_char, self.escape_char + self.separator_char)
            value = value.replace(self.line_terminator, self.escape_char + self.line_terminator)
        elif value.startswith(self.comment_char) or self.separator_char in value or self.line_terminator in value:
            raise ValueError(value)
        return value
