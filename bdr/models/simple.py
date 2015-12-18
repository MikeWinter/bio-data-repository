"""
This module contains class definitions for proxy models relating to simple type
formats.
"""

try:
    # noinspection PyPep8Naming
    import cPickle as pickle
except ImportError:
    import pickle

from .base import Format, Revision

__all__ = ["SimpleFormat", "SimpleRevision"]
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


class SettingDescriptor(object):
    """
    Provides the transparent encoding and decoding of pickled metadata stored
    in a format definition.
    """

    def __init__(self, name, default=None):
        self.default = default
        self.name = name

    @staticmethod
    def decode(data):
        """
        Decode the metadata dictionary encoded in ``data``.

        :param data: The encoded binary data.
        :type data: memoryview | buffer
        :return: The decoded metadata dictionary.
        :rtype: dict of str
        """
        string = data.tobytes() if isinstance(data, memoryview) else str(data)
        return pickle.loads(string) if string else {}

    @staticmethod
    def encode(data):
        """
        Encode the metadata dictionary in ``data``.

        :param data: The metadata dictionary.
        :type data: dict of str
        :return: The encoded binary data.
        :rtype: str
        """
        return pickle.dumps(data, pickle.HIGHEST_PROTOCOL)

    # noinspection PyUnusedLocal
    # cls is a required argument but not useful in this instance
    def __get__(self, obj, cls):
        if obj is None:
            return self
        data = self.decode(obj.metadata)
        return data.get(self.name, self.default)

    def __set__(self, obj, value):
        # noinspection PyTypeChecker
        data = self.decode(obj.metadata)
        data[self.name] = value
        obj.metadata = self.encode(data)

    def __delete__(self, obj):
        # noinspection PyTypeChecker
        data = self.decode(obj.metadata)
        del data[self.name]
        obj.metadata = self.encode(data)


class StringSettingDescriptor(SettingDescriptor):
    """
    Provides the transparent encoding and decoding of pickled strings stored
    in a format definition.

    If the value of this setting is not a character or Unicode string, an
    exception will be raised.
    """

    def __set__(self, obj, value):
        if not isinstance(value, basestring):
            raise TypeError("Must be a character or Unicode string")
        super(StringSettingDescriptor, self).__set__(obj, value)


class CharacterSettingDescriptor(StringSettingDescriptor):
    """
    Provides the transparent encoding and decoding of pickled characters stored
    in a format definition.

    If the value of this setting is not a single byte or Unicode character, an
    exception will be raised.
    """

    def __set__(self, obj, value):
        if len(value) > 1:
            raise ValueError("Must be a single character")
        super(CharacterSettingDescriptor, self).__set__(obj, value)


class SimpleFormat(Format):
    """
    Represents an instance of a simple format for files stored in the
    repository.

    This class overrides the :py:meth:`~Format.reader` and
    :py:meth:`~Format.converter` methods of the :py:class:`Format` class.
    """

    comment = CharacterSettingDescriptor("comment")
    """
    The character used to mark a line as a comment.

    By default, all lines are considered to contain data.
    """
    escape = CharacterSettingDescriptor("escape")
    """
    The character used to escape the ``separator`` if no ``quote`` has been
    defined, or the ``quote`` if it appears in a field value.

    By default, no escaping is performed.
    """
    fields = SettingDescriptor("fields")
    """
    A list of field definitions for this format.
    """
    quote = CharacterSettingDescriptor("quote")
    """
    The character used to quote values containing other special characters.

    By default, no quoting is performed.
    """
    separator = CharacterSettingDescriptor("separator", ",")
    """
    The character used to separate fields.

    Defaults to a comma (,).
    """

    def reader(self, data):
        """
        Return a :py:class:`Reader` over the given file using this format.

        :param data: A readable data file.
        :type data: django.core.files.File
        :return: A suitable ``Reader`` instance.
        :rtype: bdr.formats.Reader
        :raise ImportError: if this format does not have an associated Reader
                            class.
        """
        from ..formats.simple import Reader
        fields = [field["name"] for field in self.fields]
        return Reader(data, comment=self.comment, escape=self.escape, fields=fields, quote=self.quote,
                      separator=self.separator)

    def converter(self, reader, field_names, **kwargs):
        """
        Return a :py:class:`Converter` over the given format reader.

        :param reader: A format reader.
        :type reader: Reader
        :param field_names: An iterable that contains the names of fields to be
                            read from ``reader``.
        :type field_names: list of str | tuple of str
        :param kwargs: Additional format-dependent arguments for initialising
                       the converter.
        :type kwargs: dict of str
        :return: A suitable ``Converter`` instance.
        :rtype: bdr.formats.Converter
        :raise ImportError: if this format does not have an associated
                            ``Converter`` class.
        """
        from ..formats.simple import Converter
        return Converter(reader, field_names, **kwargs)

    class Meta(object):
        """Metadata options for the ``SimpleFormat`` model class."""

        proxy = True


class SimpleRevision(Revision):
    """
    Represents revisions of files maintained by this repository that use a
    simple format type.
    """

    @property
    def format(self):
        """The format of this revision."""
        if self._format.entry_point_name != "simple":
            raise TypeError("Not a simple format type")
        return SimpleFormat.objects.get(pk=self._format.pk)

    def merge(self, key_name, fields, other, other_key_name, other_fields, mapping=None):
        """
        Merge this revision with another by performing a natural join over key
        fields.

        It is possible to merge revisions from other files so long as the
        formats are compatible.

        :param key_name: The name of the field containing keys in this
                         revision.
        :type key_name: str | unicode
        :param fields: An iterable containing the field names to include from
                       this revision.
        :type fields: collections.Iterable of (str | unicode)
        :param other: The other revision with which this instance is to be
                      merged. This may be from a different file.
        :type other: SimpleRevision
        :param other_key_name: The name of the field containing keys in the
                               other revision.
        :type other_key_name: str | unicode
        :param other_fields: An iterable containing the field names to include
                             from the other revision.
        :type other_fields: collections.Iterable of (str | unicode)
        :param mapping: (Optional) A map from key aliases to the canonical
                        representation of those keys.
        :type mapping: dict of str
        :return: The merged data.
        """
        from ..formats.simple import Record
        if mapping is None:
            mapping = {}
        for record in self.format.reader(self.data):
            key = mapping.get(record[key_name], record[key_name])
            for other_record in other.format.reader(other.data):
                if key != mapping.get(other_record[other_key_name], other_record[other_key_name]):
                    continue

    class Meta(object):
        """Metadata options for the ``SimpleRevision`` model class."""

        proxy = True
