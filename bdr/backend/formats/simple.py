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

import csv

from . import Converter as BaseConverter, Reader as BaseReader, Record as BaseRecord


class Record(BaseRecord):
    """
    Represents a record within a simple, columnar data file composed of one or more fields.
    """
    def __init__(self, names, data):
        self._fields = names
        self._data = dict(zip(names, data))


class Reader(BaseReader):
    """
    Parses line-based, columnar files into discrete records.

    Instances of this type are iterable, returning records in file order.
    """
    def __init__(self, *args):
        super(Reader, self).__init__(*args)
        options = {'delimiter': str(self._format.separator)}
        if self._format.quote:
            options.update(quotechar=str(self._format.quote))
        else:
            options.update(quoting=csv.QUOTE_NONE)
        self._dialect = csv.reader(self._file, **options)

    def __iter__(self):
        """
        :raises IOError: if the number of parsed columns does not match that specified by the format definition.
        """
        comment_char = self._format.comment
        field_names = [field.name for field in self._format.fields.all()]
        for data in self._dialect:
            if comment_char and data[0].startswith(comment_char):
                continue
            if len(data) != len(field_names):
                raise IOError("Unrecognised format")
            yield Record(field_names, data)


class Converter(BaseConverter):
    """
    Converts records to nominally identical types, but with the option to elide fields.
    """
    def __init__(self, *args, **kwargs):
        super(Converter, self).__init__(*args, **kwargs)
        self.separator = self._format.separator
        self.quote_char = self._format.quote

    def __iter__(self):
        for record in self._reader:
            values = []
            for field_name in self._fields:
                value = record.get(field_name)
                if self.quote_char and self.separator in value:
                    values.append("{0}{1}{0}".format(self.quote_char, value))
                else:
                    values.append(value)

            yield self.separator.join(values) + '\r\n'
